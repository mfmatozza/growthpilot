"""Module 1: crawl -> site profile -> candidate keywords -> enrichment ->
opportunity score -> persist as `candidate` Keyword rows for human review.

Split into small, independently-testable functions per the brief's request
for testable parsing/scoring logic; `run_keyword_research` is the only piece
that touches the DB or does network I/O, everything else is pure given its
inputs.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.keyword import Keyword, KeywordStatus
from app.models.site import Site
from app.pipelines.scoring import opportunity_score
from app.services.crawler.base import PageFetcher
from app.services.crawler.site_crawler import PageContent, crawl_site
from app.services.keyword_data.base import KeywordDataProvider
from app.services.llm.base import LLMClient

_SITE_PROFILE_SYSTEM = (
    "You are a B2B/B2C content strategist analyzing a website's crawled pages. "
    "Respond only via the emit_result tool call with this exact JSON shape: "
    '{"business_summary": string, "target_audience": string, '
    '"existing_topics": string[], "tone": string, "content_gaps": string[]}. '
    "content_gaps should name topics competitors in this space typically cover "
    "that this site's crawled pages do not."
)

_KEYWORD_CANDIDATES_SYSTEM = (
    "You are an SEO strategist generating informational keyword/topic ideas, with a strong bias toward "
    "long-tail keywords — specific, multi-word phrases with clear search intent and lower competition. "
    "Long-tail phrases are what actually get a smaller or newer site found in organic search; broad "
    "head terms (1-2 generic words) are dominated by sites with far more domain authority and rarely "
    "convert into real traffic for a site like this. "
    "Respond only via the emit_result tool call with this exact JSON shape: "
    '{"keywords": [{"keyword": string, "rationale": string, "relevance_score": number}]}. '
    "relevance_score is 0-100, your judgment of how directly this topic serves "
    "the site's target audience and business. Generate between 30 and 50 items, and make at least "
    "two-thirds of them genuine long-tail phrases (four or more words, specific enough that they "
    "plausibly rank without needing high domain authority) rather than short generic head terms."
)


def build_site_profile_prompt(pages: list[PageContent]) -> str:
    sections = []
    for page in pages:
        sections.append(
            f"URL: {page.url}\n"
            f"Title: {page.title}\n"
            f"Meta description: {page.meta_description}\n"
            f"H1: {', '.join(page.h1) or '(none)'}\n"
            f"H2: {', '.join(page.h2) or '(none)'}\n"
            f"Excerpt: {page.text_excerpt[:800]}"
        )
    return "Analyze this crawled site and produce the business profile.\n\n" + "\n\n---\n\n".join(sections)


def parse_site_profile(raw: dict) -> dict:
    """Defensive normalization of the LLM's JSON output — never trust an
    external model to always match the requested shape exactly."""
    return {
        "business_summary": str(raw.get("business_summary", "")).strip(),
        "target_audience": str(raw.get("target_audience", "")).strip(),
        "existing_topics": [str(t) for t in raw.get("existing_topics", []) if t],
        "tone": str(raw.get("tone", "")).strip(),
        "content_gaps": [str(t) for t in raw.get("content_gaps", []) if t],
    }


def build_keyword_candidates_prompt(profile: dict, existing_keywords: list[str] | None = None) -> str:
    prompt = (
        "Business summary: " + profile.get("business_summary", "") + "\n"
        "Target audience: " + profile.get("target_audience", "") + "\n"
        "Existing content topics: " + ", ".join(profile.get("existing_topics", [])) + "\n"
        "Known content gaps: " + ", ".join(profile.get("content_gaps", [])) + "\n\n"
        "Generate 30-50 informational keyword/topic candidates this business should "
        "target, each with a one-sentence rationale. Most should be long-tail phrases, per your instructions."
    )
    if existing_keywords:
        prompt += (
            "\n\nAlready targeting these from a previous run — do not repeat them or suggest close "
            "variants of them: " + ", ".join(existing_keywords)
        )
    return prompt


def parse_keyword_candidates(raw: dict) -> list[dict]:
    """Defensive normalization + dedup. Drops entries missing a keyword
    string rather than raising, since a partially-malformed LLM response
    shouldn't discard the whole batch."""
    candidates: list[dict] = []
    seen: set[str] = set()

    for item in raw.get("keywords", []):
        keyword = str(item.get("keyword", "")).strip()
        if not keyword or keyword.lower() in seen:
            continue
        seen.add(keyword.lower())
        try:
            relevance = float(item.get("relevance_score", 0))
        except (TypeError, ValueError):
            relevance = 0.0
        candidates.append(
            {
                "keyword": keyword,
                "rationale": str(item.get("rationale", "")).strip(),
                "relevance_score": max(0.0, min(100.0, relevance)),
            }
        )
    return candidates


def analyze_site(pages: list[PageContent], llm: LLMClient) -> dict:
    raw = llm.complete_json(system=_SITE_PROFILE_SYSTEM, user=build_site_profile_prompt(pages))
    return parse_site_profile(raw)


def generate_keyword_candidates(profile: dict, llm: LLMClient, existing_keywords: list[str] | None = None) -> list[dict]:
    raw = llm.complete_json(
        system=_KEYWORD_CANDIDATES_SYSTEM, user=build_keyword_candidates_prompt(profile, existing_keywords)
    )
    return parse_keyword_candidates(raw)


def dedupe_against_existing(candidates: list[dict], existing_keywords: list[str]) -> list[dict]:
    """Belt-and-suspenders on top of asking the model not to repeat itself
    (build_keyword_candidates_prompt) — it doesn't always listen, confirmed
    by a real site accumulating near-duplicate candidates across repeated
    runs. Exact case-insensitive match only; doesn't try to catch near-dupes."""
    existing_lower = {k.lower() for k in existing_keywords}
    return [c for c in candidates if c["keyword"].lower() not in existing_lower]


def enrich_candidates(candidates: list[dict], provider: KeywordDataProvider) -> list[dict]:
    """Attaches volume/difficulty/opportunity_score. If the provider call
    fails for the whole batch, callers should catch KeywordDataError
    upstream and still persist candidates with null metrics rather than
    losing the LLM's work — see run_keyword_research."""
    metrics_by_keyword = {m.keyword: m for m in provider.get_metrics([c["keyword"] for c in candidates])}

    enriched = []
    for candidate in candidates:
        metrics = metrics_by_keyword.get(candidate["keyword"])
        volume = metrics.volume if metrics else None
        difficulty = metrics.difficulty if metrics else None
        enriched.append(
            {
                **candidate,
                "volume": volume,
                "difficulty": difficulty,
                "opportunity_score": opportunity_score(
                    volume=volume, difficulty=difficulty, relevance_score=candidate["relevance_score"]
                ),
            }
        )
    return enriched


def run_keyword_research(
    *,
    db: Session,
    site: Site,
    fetcher: PageFetcher,
    llm: LLMClient,
    keyword_data_provider: KeywordDataProvider | None,
) -> list[Keyword]:
    """Full Module 1 pipeline for one site. `keyword_data_provider=None`
    skips enrichment (e.g. no DataForSEO key configured yet) — candidates
    are still generated and stored with null volume/difficulty so the human
    review step isn't blocked on that integration."""
    pages = crawl_site(site.url, fetcher)
    profile = analyze_site(pages, llm)
    site.profile = profile
    db.add(site)

    existing_keywords = list(db.scalars(select(Keyword.keyword).where(Keyword.site_id == site.id)).all())
    # Capped in the prompt to keep it from growing unbounded after many runs —
    # the post-generation dedupe below still checks against the full set.
    candidates = generate_keyword_candidates(profile, llm, existing_keywords=existing_keywords[:200])
    candidates = dedupe_against_existing(candidates, existing_keywords)

    if keyword_data_provider is not None:
        candidates = enrich_candidates(candidates, keyword_data_provider)
    else:
        candidates = [
            {**c, "volume": None, "difficulty": None, "opportunity_score": opportunity_score(
                volume=None, difficulty=None, relevance_score=c["relevance_score"]
            )}
            for c in candidates
        ]

    rows = [
        Keyword(
            site_id=site.id,
            keyword=c["keyword"],
            rationale=c["rationale"],
            volume=c["volume"],
            difficulty=c["difficulty"],
            relevance_score=c["relevance_score"],
            opportunity_score=c["opportunity_score"],
            status=KeywordStatus.candidate,
        )
        for c in candidates
    ]
    db.add_all(rows)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


__all__ = [
    "analyze_site",
    "generate_keyword_candidates",
    "dedupe_against_existing",
    "enrich_candidates",
    "run_keyword_research",
    "build_site_profile_prompt",
    "parse_site_profile",
    "build_keyword_candidates_prompt",
    "parse_keyword_candidates",
]
