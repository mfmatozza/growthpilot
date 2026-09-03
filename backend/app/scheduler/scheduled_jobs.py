"""Weekly automation for Modules 3 and 4 — registered in app/main.py's
lifespan via app/scheduler/jobs.py. Runs inside the same backend process
(APScheduler's BackgroundScheduler), so once the backend is deployed this
needs nothing else: no external cron, no separate service, no manual
trigger. Each site is wrapped in its own try/except so one site's failure
(a down page, a rate-limited API) doesn't take out the rest of the run.
"""

import logging

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.article import Article
from app.models.keyword import Keyword, KeywordStatus
from app.models.site import Site
from app.pipelines.article_generation import run_generate_article
from app.pipelines.geo_tracker import get_available_providers, run_geo_check
from app.pipelines.reddit_monitor import run_reddit_monitor
from app.pipelines.technical_audit import run_technical_audit
from app.services.crawler.httpx_fetcher import HttpxFetcher
from app.services.llm.base import LLMError
from app.services.llm.factory import get_default_llm_client
from app.services.reddit.base import RedditError
from app.services.reddit.praw_client import PrawRedditClient
from app.services.serp.base import SerpError
from app.services.serp.serpapi import SerpApiProvider

logger = logging.getLogger(__name__)


def run_weekly_audits() -> None:
    db = SessionLocal()
    try:
        try:
            llm = get_default_llm_client()
        except LLMError:
            logger.info("Skipping weekly technical audits — no LLM provider configured")
            return

        settings = get_settings()
        sites = db.scalars(select(Site)).all()
        for site in sites:
            try:
                run_technical_audit(
                    db=db, site=site, fetcher=HttpxFetcher(), llm=llm, pagespeed_api_key=settings.google_pagespeed_api_key
                )
            except Exception:
                logger.exception("Weekly technical audit failed for site %s (%s)", site.id, site.url)
    finally:
        db.close()


def run_weekly_geo_checks() -> None:
    db = SessionLocal()
    try:
        providers = get_available_providers()
        if not providers:
            logger.info("Skipping weekly GEO checks — no GEO provider API key configured")
            return
        try:
            analysis_llm = get_default_llm_client()
        except LLMError:
            logger.info("Skipping weekly GEO checks — no default LLM configured for mention analysis")
            return

        sites = db.scalars(select(Site)).all()
        for site in sites:
            try:
                run_geo_check(db=db, site=site, providers=providers, analysis_llm=analysis_llm)
            except Exception:
                logger.exception("Weekly GEO check failed for site %s (%s)", site.id, site.url)
    finally:
        db.close()


def run_weekly_reddit_monitor() -> None:
    db = SessionLocal()
    try:
        try:
            reddit_client = PrawRedditClient()
        except RedditError:
            logger.info("Skipping weekly Reddit monitor — REDDIT_CLIENT_ID/REDDIT_CLIENT_SECRET not configured")
            return
        try:
            llm = get_default_llm_client()
        except LLMError:
            logger.info("Skipping weekly Reddit monitor — no default LLM configured for draft replies")
            return

        sites = db.scalars(select(Site)).all()
        for site in sites:
            if not site.subreddits:
                continue
            try:
                run_reddit_monitor(db=db, site=site, reddit_client=reddit_client, llm=llm)
            except Exception:
                logger.exception("Weekly Reddit monitor failed for site %s (%s)", site.id, site.url)
    finally:
        db.close()


# Capped per site per run — an LLM call per outline plus one per section
# (5-8 sections) adds up fast across many sites/keywords; this bounds both
# cost and how long the weekly job runs for.
_MAX_ARTICLE_DRAFTS_PER_SITE_PER_RUN = 2


def run_weekly_article_drafts() -> None:
    """Auto-drafts articles for approved keywords that don't have one yet —
    never auto-publishes (drafts still need a human to move them to
    review/published, see app/api/routes/articles.py)."""
    db = SessionLocal()
    try:
        try:
            llm = get_default_llm_client()
        except LLMError:
            logger.info("Skipping weekly article drafts — no LLM provider configured")
            return

        serp_provider = None
        try:
            serp_provider = SerpApiProvider()
        except SerpError:
            pass  # optional — see docs/DECISIONS.md #25

        sites = db.scalars(select(Site)).all()
        for site in sites:
            try:
                stmt = (
                    select(Keyword)
                    .outerjoin(Article, Article.keyword_id == Keyword.id)
                    .where(Keyword.site_id == site.id, Keyword.status == KeywordStatus.approved, Article.id.is_(None))
                    .order_by(Keyword.opportunity_score.desc().nullslast())
                    .limit(_MAX_ARTICLE_DRAFTS_PER_SITE_PER_RUN)
                )
                for keyword in db.scalars(stmt).all():
                    run_generate_article(
                        db=db, site=site, keyword=keyword, llm=llm, fetcher=HttpxFetcher(), serp_provider=serp_provider
                    )
            except Exception:
                logger.exception("Weekly article draft failed for site %s (%s)", site.id, site.url)
    finally:
        db.close()
