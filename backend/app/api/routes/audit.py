from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.audit_finding import AuditFinding
from app.models.site import Site
from app.pipelines.technical_audit import run_technical_audit
from app.schemas.audit import AuditFindingRead, RunAuditRequest
from app.services.audit.export import build_findings_csv
from app.services.crawler.base import FetchError
from app.services.crawler.httpx_fetcher import HttpxFetcher
from app.services.llm.base import LLMError
from app.services.llm.factory import get_default_llm_client

router = APIRouter(prefix="/api/audit-findings", tags=["audit"])


def _findings_query(site_id: int | None):
    stmt = select(AuditFinding).order_by(AuditFinding.severity, AuditFinding.first_seen.desc())
    if site_id is not None:
        stmt = stmt.where(AuditFinding.site_id == site_id)
    return stmt


@router.get("", response_model=list[AuditFindingRead])
def list_findings(site_id: int | None = None, db: Session = Depends(get_db)) -> list[AuditFinding]:
    return list(db.scalars(_findings_query(site_id)).all())


@router.get("/export")
def export_findings(site_id: int | None = None, db: Session = Depends(get_db)) -> Response:
    """CSV export of every finding (open and resolved) — the list view
    only shows open ones, this is the full record for reporting/archiving."""
    findings = list(db.scalars(_findings_query(site_id)).all())
    filename = f"audit-findings-site-{site_id}.csv" if site_id is not None else "audit-findings.csv"
    return Response(
        content=build_findings_csv(findings),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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

    try:
        return run_technical_audit(
            db=db,
            site=site,
            fetcher=HttpxFetcher(),
            llm=llm,
            pagespeed_api_key=get_settings().google_pagespeed_api_key,
        )
    except FetchError as exc:
        raise HTTPException(status_code=502, detail=f"Couldn't reach {site.url}: {exc}") from exc
