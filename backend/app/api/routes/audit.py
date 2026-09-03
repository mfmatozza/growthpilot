from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.audit_finding import AuditFinding
from app.schemas.audit import AuditFindingRead

router = APIRouter(prefix="/api/audit-findings", tags=["audit"])

# Read-only for now. Module 3 (Lighthouse + crawl-based auditor) is not
# built yet — see build order in the project brief.


@router.get("", response_model=list[AuditFindingRead])
def list_findings(site_id: int | None = None, db: Session = Depends(get_db)) -> list[AuditFinding]:
    stmt = select(AuditFinding).order_by(AuditFinding.severity, AuditFinding.first_seen.desc())
    if site_id is not None:
        stmt = stmt.where(AuditFinding.site_id == site_id)
    return list(db.scalars(stmt).all())
