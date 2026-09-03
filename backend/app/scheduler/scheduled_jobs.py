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
from app.models.site import Site
from app.pipelines.geo_tracker import get_available_providers, run_geo_check
from app.pipelines.technical_audit import run_technical_audit
from app.services.crawler.httpx_fetcher import HttpxFetcher
from app.services.llm.base import LLMError
from app.services.llm.factory import get_default_llm_client

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
