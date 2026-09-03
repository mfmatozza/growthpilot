import csv
import io

from app.models.audit_finding import AuditFinding

_HEADER = ["page", "severity", "description", "status", "first_seen", "resolved_at"]


def build_findings_csv(findings: list[AuditFinding]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(_HEADER)
    for f in findings:
        writer.writerow(
            [
                f.page,
                f.severity.value,
                f.description,
                "resolved" if f.resolved_at else "open",
                f.first_seen.isoformat(),
                f.resolved_at.isoformat() if f.resolved_at else "",
            ]
        )
    return output.getvalue()
