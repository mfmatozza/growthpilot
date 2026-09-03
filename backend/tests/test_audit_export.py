from datetime import datetime, timezone

from app.models.audit_finding import AuditFinding, Severity
from app.services.audit.export import build_findings_csv


def _finding(**overrides) -> AuditFinding:
    defaults = dict(
        site_id=1,
        page="https://acme.com",
        severity=Severity.high,
        description="Missing alt text",
        first_seen=datetime(2026, 1, 1, tzinfo=timezone.utc),
        resolved_at=None,
    )
    return AuditFinding(**{**defaults, **overrides})


def test_build_findings_csv_header():
    csv_text = build_findings_csv([])
    assert csv_text.strip() == "page,severity,description,status,first_seen,resolved_at"


def test_build_findings_csv_open_finding_has_empty_resolved_at():
    csv_text = build_findings_csv([_finding()])
    lines = csv_text.strip().splitlines()
    assert lines[1] == "https://acme.com,high,Missing alt text,open,2026-01-01T00:00:00+00:00,"


def test_build_findings_csv_resolved_finding():
    resolved = _finding(resolved_at=datetime(2026, 1, 5, tzinfo=timezone.utc))
    csv_text = build_findings_csv([resolved])
    assert ",resolved,2026-01-01T00:00:00+00:00,2026-01-05T00:00:00+00:00" in csv_text


def test_build_findings_csv_escapes_commas_in_description():
    csv_text = build_findings_csv([_finding(description="Missing title, meta, and alt text")])
    assert '"Missing title, meta, and alt text"' in csv_text
