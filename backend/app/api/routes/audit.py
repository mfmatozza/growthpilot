from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.audit_finding import AuditFinding
from app.models.site import Site
from app.pipelines.technical_audit import run_technical_audit
from app.schemas.audit import AuditFindingRead, RunAuditRequest
from app.services.crawler.httpx_fetcher import HttpxFetcher
from app.services.llm.base import LLMError
from app.services.llm.factory import get_default_llm_client

router = APIRouter(prefix="/api/audit-findings", tags=["audit"])


@router.get("", response_model=list[AuditFindingRead])
def list_findings(site_id: int | None = None, db: Session = Depends(get_db)) -> list[AuditFinding]:
    stmt = select(AuditFinding).order_by(AuditFinding.severity, AuditFinding.first_seen.desc())
    if site_id is not None:
        stmt = stmt.where(AuditFinding.site_id == site_id)
    return list(db.scalars(stmt).all())


@router.post("/run", response_model=list[AuditFindingRead], status_code=201)
def trigger_audit(payload: RunAuditRequest, db: Session = Depends(get_db)) -> list[AuditFinding]:
    """Runs synchronously — a crawl of a handful of pages plus one PageSpeed
    call, same tradeoff noted on the other /run endpoints."""
    site = db.get(Site, payload.site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    try:
        llm = get_default_llm_client()
    except LLMError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return run_technical_audit(
        db=db,
        site=site,
        fetcher=HttpxFetcher(),
        llm=llm,
        pagespeed_api_key=get_settings().google_pagespeed_api_key,
    )
