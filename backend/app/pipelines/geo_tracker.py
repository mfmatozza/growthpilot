"""Module 4: for each of a site's top approved keywords, ask each available
AI-search provider the query verbatim, then have an LLM analyze whether the
site's brand was mentioned and who else was. Providers with no API key
configured are skipped, not fatal — see get_available_providers.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.geo_mention import GeoMention, GeoProvider
from app.models.keyword import Keyword, KeywordStatus
from app.models.site import Site
from app.services.llm.base import LLMClient, LLMError

logger = logging.getLogger(__name__)

_ANALYSIS_SYSTEM = (
    "You analyze an AI assistant's answer to a search-style query for brand mentions. "
    "Respond only via the emit_result tool call with this exact JSON shape: "
    '{"mentioned": boolean, "context_snippet": string, "competitors": string[]}. '
    "context_snippet is a short quote or paraphrase of how the brand was mentioned (empty string if not "
    "mentioned). competitors are other named companies/products/tools mentioned as alternatives to it."
)

_ANSWER_SYSTEM = "Answer the user's question naturally and concisely, the way you normally would."


def get_available_providers() -> dict[GeoProvider, LLMClient]:
    """Instantiates a client for every GEO provider that has an API key
    configured. Import inside the function so a missing optional dependency
    (none currently, but keeps the pattern consistent) can't break import of
    this module."""
    from app.services.llm.anthropic_client import AnthropicClient
    from app.services.llm.gemini_client import GeminiClient
    from app.services.llm.openai_client import OpenAIClient
    from app.services.llm.perplexity_client import PerplexityClient

    candidates: dict[GeoProvider, type[LLMClient]] = {
        GeoProvider.chatgpt: OpenAIClient,
        GeoProvider.claude: AnthropicClient,
        GeoProvider.gemini: GeminiClient,
        GeoProvider.perplexity: PerplexityClient,
    }
    available: dict[GeoProvider, LLMClient] = {}
    for provider, client_cls in candidates.items():
        try:
            available[provider] = client_cls()
        except LLMError:
            logger.info("GEO provider %s has no API key configured — skipping", provider.value)
    return available


def build_analysis_prompt(site: Site, query: str, answer: str) -> str:
    return f"Brand to check for: {site.name} ({site.url})\nQuery asked: {query}\n\nAnswer received:\n{answer}"


def parse_mention_analysis(raw: dict) -> dict:
    return {
        "mentioned": bool(raw.get("mentioned", False)),
        "context_snippet": str(raw.get("context_snippet", "")).strip() or None,
        "competitors": [str(c) for c in raw.get("competitors", []) if c],
    }


def analyze_mention(site: Site, query: str, answer: str, analysis_llm: LLMClient) -> dict:
    raw = analysis_llm.complete_json(system=_ANALYSIS_SYSTEM, user=build_analysis_prompt(site, query, answer))
    return parse_mention_analysis(raw)


def select_target_queries(db: Session, site: Site, limit: int = 10) -> list[str]:
    """Seeded from Module 1's approved keywords, per the brief — ranked by
    opportunity score so the highest-value queries get checked first when
    there are more approved keywords than the per-run cap."""
    stmt = (
        select(Keyword)
        .where(Keyword.site_id == site.id, Keyword.status == KeywordStatus.approved)
        .order_by(Keyword.opportunity_score.desc().nullslast())
        .limit(limit)
    )
    return [k.keyword for k in db.scalars(stmt).all()]


def run_geo_check(
    *,
    db: Session,
    site: Site,
    providers: dict[GeoProvider, LLMClient],
    analysis_llm: LLMClient,
    max_queries: int = 10,
) -> list[GeoMention]:
    queries = select_target_queries(db, site, limit=max_queries)
    rows: list[GeoMention] = []

    for query in queries:
        for provider, client in providers.items():
            try:
                answer = client.complete_text(system=_ANSWER_SYSTEM, user=query)
                analysis = analyze_mention(site, query, answer, analysis_llm)
            except LLMError as exc:
                logger.warning("GEO check failed for %s / %s: %s", provider.value, query, exc)
                continue

            row = GeoMention(
                site_id=site.id,
                query=query,
                provider=provider,
                mentioned=analysis["mentioned"],
                context_snippet=analysis["context_snippet"],
                competitors_mentioned=analysis["competitors"],
            )
            db.add(row)
            rows.append(row)

    db.commit()
    for row in rows:
        db.refresh(row)
    return rows
