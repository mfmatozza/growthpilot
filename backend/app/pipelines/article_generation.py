"""Module 2: outline -> section-by-section draft -> internal linking pass,
output as clean Markdown (no inline styling, no images — see
docs/DECISIONS.md #26). Comparison mode uses a distinct prompt template
per the brief. SERP research only runs when SERPAPI_KEY is configured —
see docs/DECISIONS.md #25 for why there's no free scraper fallback.
"""

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article, ArticleStatus, ArticleType
from app.models.keyword import Keyword
from app.models.site import Site
from app.services.crawler.base import FetchError, PageFetcher
from app.services.crawler.site_crawler import PageContent, extract_page_content
from app.services.llm.base import LLMClient
from app.services.serp.base import SerpError, SerpProvider

# Applied to every generation prompt. The em-dash rule and stock-phrase list
# are the direct, explicit ask; strip_em_dashes() below is the backstop for
# when the model does it anyway.
_HUMAN_VOICE_INSTRUCTION = (
    "Write like a knowledgeable person, not an AI assistant. Hard rule: never use an em dash (—) or a "
    "spaced hyphen as a connector anywhere — use a period, comma, colon, or 'and'/'but' instead. Avoid "
    "stock AI phrasing: \"in today's fast-paced world\", \"when it comes to X\", \"it's important to note "
    "that\", \"in conclusion\", \"unlock the power of\", forced rule-of-three lists, and mechanical "
    "\"on one hand / on the other hand\" balance. Vary sentence length the way a person actually writes. "
    "Do not include images, image placeholders, or alt-text markers — text only."
)

_FACT_CHECK_NOTE = (
    "If you state a specific statistic, date, dollar figure, or named-source claim you are not highly "
    "confident is accurate, tag it immediately with [VERIFY] right after it, e.g. '73% of users [VERIFY]'. "
    "Never invent a precise-sounding statistic without that tag — a human reviews every draft before "
    "publishing, and this is what they'll check first."
)

_LENGTH_INSTRUCTION = (
    "Keep the whole article well under 2000 words total, shorter if the topic allows it — this is a hard "
    "constraint, not a suggestion. Every sentence should earn its place; cut padding, throat-clearing, and "
    "restating the same point twice."
)

_OUTLINE_SYSTEM = (
    "You are an SEO content strategist producing a tight, focused article outline for a target keyword. "
    "Respond only via the emit_result tool call with this exact JSON shape: "
    '{"title": string, "sections": [{"heading": string, "key_points": string[]}], '
    '"differentiation_angle": string}. Produce 4-5 sections covering what genuinely useful content on this '
    "topic needs — if competitor page structures are provided, use them as a reference for coverage; "
    "otherwise rely on your own knowledge of what a thorough answer to this query looks like. Favor fewer, "
    "denser sections over many thin ones. " + _LENGTH_INSTRUCTION + " "
    "differentiation_angle is one genuine way this article can be more useful than typical results for "
    "this query (a sharper angle, more specific advice, or a real content gap). " + _HUMAN_VOICE_INSTRUCTION
)

_COMPARISON_OUTLINE_SYSTEM = (
    "You are an SEO content strategist producing an outline for an UNBIASED multi-option comparison "
    "article. Respond only via the emit_result tool call with this exact JSON shape: "
    '{"title": string, "sections": [{"heading": string, "key_points": string[]}], '
    '"differentiation_angle": string}. Structure: a brief intro section framing the decision, a section '
    "listing comparison criteria, one compact section per option being compared (3 options is enough — "
    "infer genuinely relevant options for this topic, not just the site's own product), a section "
    "presenting a Markdown comparison table across the criteria, and a short closing verdict section "
    "recommending different options for different use cases. This must be genuinely unbiased — call out "
    "real tradeoffs and situations where the site's own product/service is NOT the best fit, if it's one "
    "of the options. " + _LENGTH_INSTRUCTION + " "
    "differentiation_angle should describe what makes this comparison more useful than a typical listicle. "
    + _HUMAN_VOICE_INSTRUCTION
)

_SECTION_DRAFTING_SYSTEM = (
    "You write one section of an article in Markdown, given the article's outline and any prior sections "
    "already written (for continuity — don't repeat what's already covered). Write the section body only — "
    "no heading line (added separately), no meta-commentary about what you're doing. Be specific and "
    "genuinely useful, not filler. Aim for roughly 100-180 words for this section — short and dense, not a "
    "full essay; the whole article across all sections needs to land well under 2000 words. "
    + _HUMAN_VOICE_INSTRUCTION + " " + _FACT_CHECK_NOTE
)

_INTERNAL_LINK_SYSTEM = (
    "You insert internal links into an article's Markdown body, naturally, where relevant. You're given a "
    "list of existing published pages (title + relative URL). Insert 2-5 Markdown links "
    "([anchor text](url)) where a mention genuinely relates to one of those pages — never force it, never "
    "link the same page twice, never invent a URL not in the list. Respond only via the emit_result tool "
    'call with this exact JSON shape: {"body_markdown": string} — the FULL article body with links '
    "inserted, otherwise character-for-character unchanged."
)


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "article"


def strip_em_dashes(text: str) -> str:
    """Backstop for _HUMAN_VOICE_INSTRUCTION — models slip. A comma reads
    naturally in the large majority of em/en-dash usages (they're most
    often standing in for a comma or parenthetical aside already)."""
    text = text.replace(" — ", ", ").replace("—", ", ")
    text = text.replace(" – ", ", ")
    return text


def crawl_competitor_pages(urls: list[str], fetcher: PageFetcher, max_pages: int = 6) -> list[PageContent]:
    pages = []
    for url in urls[:max_pages]:
        try:
            fetched = fetcher.fetch(url)
        except FetchError:
            continue
        pages.append(extract_page_content(fetched.url, fetched.html))
    return pages


def research_competitor_structure(
    keyword: str, serp_provider: SerpProvider | None, fetcher: PageFetcher
) -> list[PageContent]:
    """Empty list (not an error) if no provider is configured or the
    provider call fails — outline generation is written to work either
    way, just with less input. See docs/DECISIONS.md #25."""
    if serp_provider is None:
        return []
    try:
        urls = serp_provider.top_results(keyword)
    except SerpError:
        return []
    return crawl_competitor_pages(urls, fetcher)


def build_outline_prompt(keyword: str, profile: dict, competitor_pages: list[PageContent]) -> str:
    lines = [
        f"Keyword/topic: {keyword}",
        f"Business: {profile.get('business_summary', '')}",
        f"Target audience: {profile.get('target_audience', '')}",
    ]
    if profile.get("content_gaps"):
        lines.append("Known content gaps this site could address: " + ", ".join(profile["content_gaps"]))
    if competitor_pages:
        lines.append("\nTop-ranking competitor page structures for this keyword:")
        for page in competitor_pages:
            lines.append(f"- {page.title}: {', '.join(page.h2) or '(no H2s found)'}")
    else:
        lines.append("\nNo live competitor data available — rely on your own knowledge of what a thorough answer needs.")
    return "\n".join(lines)


def parse_outline(raw: dict) -> dict:
    sections = []
    for item in raw.get("sections", []):
        heading = str(item.get("heading", "")).strip()
        if not heading:
            continue
        sections.append({"heading": heading, "key_points": [str(p) for p in item.get("key_points", []) if p]})
    return {
        "title": str(raw.get("title", "")).strip(),
        "sections": sections,
        "differentiation_angle": str(raw.get("differentiation_angle", "")).strip(),
    }


def generate_outline(
    keyword: str, profile: dict, competitor_pages: list[PageContent], article_type: ArticleType, llm: LLMClient
) -> dict:
    system = _COMPARISON_OUTLINE_SYSTEM if article_type == ArticleType.comparison else _OUTLINE_SYSTEM
    raw = llm.complete_json(system=system, user=build_outline_prompt(keyword, profile, competitor_pages))
    return parse_outline(raw)


def build_section_prompt(keyword: str, outline: dict, section: dict, prior_markdown: str) -> str:
    parts = [
        f"Article topic: {keyword}",
        f"Full outline: {[s['heading'] for s in outline.get('sections', [])]}",
        f"Differentiation angle: {outline.get('differentiation_angle', '')}",
        f"Writing this section now: {section['heading']}",
        f"Key points to cover: {', '.join(section.get('key_points', []))}",
    ]
    if prior_markdown:
        parts.append(f"\nSections already written (for continuity, don't repeat):\n{prior_markdown}")
    parts.append("\nWrite this section's body now — no heading line.")
    return "\n".join(parts)


def draft_article_body(keyword: str, outline: dict, llm: LLMClient) -> str:
    written: list[str] = []
    for section in outline.get("sections", []):
        prior = "\n\n".join(written)
        body = llm.complete_text(
            system=_SECTION_DRAFTING_SYSTEM, user=build_section_prompt(keyword, outline, section, prior)
        )
        written.append(f"## {section['heading']}\n\n{body.strip()}")

    title = outline.get("title") or keyword
    return f"# {title}\n\n" + "\n\n".join(written)


def build_internal_link_prompt(body_markdown: str, candidates: list[tuple[str, str]]) -> str:
    lines = ["Existing published pages available to link to:"]
    for title, slug in candidates:
        lines.append(f"- {title}: /{slug}")
    lines.append("\nArticle body:\n" + body_markdown)
    return "\n".join(lines)


def insert_internal_links(body_markdown: str, candidates: list[tuple[str, str]], llm: LLMClient) -> str:
    if not candidates:
        return body_markdown
    raw = llm.complete_json(system=_INTERNAL_LINK_SYSTEM, user=build_internal_link_prompt(body_markdown, candidates))
    result = str(raw.get("body_markdown", "")).strip()
    return result or body_markdown  # never let a malformed response wipe out a good draft


def run_generate_article(
    *,
    db: Session,
    site: Site,
    keyword: Keyword,
    llm: LLMClient,
    fetcher: PageFetcher,
    serp_provider: SerpProvider | None = None,
    article_type: ArticleType = ArticleType.informational,
) -> Article:
    profile = site.profile or {}
    competitor_pages = research_competitor_structure(keyword.keyword, serp_provider, fetcher)
    outline = generate_outline(keyword.keyword, profile, competitor_pages, article_type, llm)
    body = draft_article_body(keyword.keyword, outline, llm)

    published = db.scalars(
        select(Article).where(Article.site_id == site.id, Article.status == ArticleStatus.published)
    ).all()
    if published:
        body = insert_internal_links(body, [(a.title, a.slug) for a in published], llm)

    body = strip_em_dashes(body)
    title = outline.get("title") or keyword.keyword

    article = Article(
        site_id=site.id,
        keyword_id=keyword.id,
        title=title,
        slug=slugify(title),
        article_type=article_type,
        outline=outline,
        body_markdown=body,
        status=ArticleStatus.draft,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article
