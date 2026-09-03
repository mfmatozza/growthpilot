from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.audit_finding import Severity


class RunAuditRequest(BaseModel):
    site_id: int


class AuditFindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    page: str
    severity: Severity
    description: str
    first_seen: datetime
    resolved_at: datetime | None
