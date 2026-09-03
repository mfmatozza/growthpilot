"""Module 3: crawl-based checks (missing meta, broken links, duplicate
titles, missing alt text) + a PageSpeed Insights pass on the homepage,
translated into a prioritized plain-English issue list via an LLM.

Each run replaces the site's open findings with a fresh snapshot (existing
unresolved findings are marked resolved, then the new set is inserted) —
simpler and more honest than trying to fuzzy-match LLM-phrased descriptions
across runs to preserve first_seen continuity. See docs/DECISIONS.md #19.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_finding import AuditFinding, Severity
from app.models.site import Site
from app.services.audit.page_analysis import check_links, crawl_for_audit, run_all_checks
from app.services.audit.pagespeed import PageSpeedError, fetch_pagespeed_report, summarize_pagespeed_report
from app.services.crawler.base import PageFetcher
from app.services.llm.base import LLMClient

_VALID_SEVERITIES = {s.value for s in Severity}

_SUMMARY_SYSTEM = (
    "You are a technical SEO auditor translating raw crawl/PageSpeed findings into a prioritized, "
    "plain-English issue list for a non-technical site owner. Respond only via the emit_result tool call "
    'with this exact JSON shape: {"findings": [{"page": string, "severity": string, "description": string}]}. '
    'severity must be exactly one of "critical", "high", "medium", "low". description should be one or two '
    "plain-English sentences explaining the impact and, where obvious, the fix — not raw technical jargon."
)


def build_summary_prompt(raw_findings: list[dict], pagespeed_summary: dict | None) -> str:
    lines = ["Raw crawl findings:"]
    for f in raw_findings:
        lines.append(f"- [{f['category']}] {f['page']}: {f['description']}")

    if pagespeed_summary:
        lines.append("\nPageSpeed Insights scores (homepage, mobile, 0-100):")
        for name, score in pagespeed_summary["scores"].items():
            lines.append(f"- {name}: {score}")
        lines.append("\nPageSpeed opportunities:")
        for o in pagespeed_summary["opportunities"]:
            lines.append(f"- {o['title']}: {o['description']}")

    return "\n".join(lines)


def parse_summary_findings(raw: dict, fallback_page: str) -> list[dict]:
    findings = []
    for item in raw.get("findings", []):
        page = str(item.get("page", "")).strip() or fallback_page
        severity = str(item.get("severity", "")).strip().lower()
        if severity not in _VALID_SEVERITIES:
            severity = "medium"
        description = str(item.get("description", "")).strip()
        if not description:
            continue
        findings.append({"page": page, "severity": severity, "description": description})
    return findings


def run_technical_audit(
    *,
    db: Session,
    site: Site,
    fetcher: PageFetcher,
    llm: LLMClient,
    pagespeed_api_key: str = "",
    max_pages: int = 8,
) -> list[AuditFinding]:
    pages = crawl_for_audit(site.url, fetcher, max_pages=max_pages)

    # dict.fromkeys, not a set: dedupes while preserving crawl order (Python
    # sets iterate in hash-randomized order per process, which made the
    # first-N-of-many cap in check_links effectively pick a different random
    # subset of links every run — confirmed against a real site, not a
    # hypothetical). Order here means "homepage's links get checked first".
    all_links = list(dict.fromkeys(link for p in pages for link in p.internal_links))
    link_statuses = check_links(all_links, fetcher)
    raw_findings = run_all_checks(pages, link_statuses)

    pagespeed_summary = None
    try:
        report = fetch_pagespeed_report(site.url, pagespeed_api_key)
        pagespeed_summary = summarize_pagespeed_report(report)
    except PageSpeedError:
        pass  # PageSpeed is a bonus signal, not required for the audit to produce findings

    if not raw_findings and not pagespeed_summary:
        summarized: list[dict] = []
    else:
        raw = llm.complete_json(system=_SUMMARY_SYSTEM, user=build_summary_prompt(raw_findings, pagespeed_summary))
        summarized = parse_summary_findings(raw, fallback_page=site.url)

    now = datetime.now(timezone.utc)
    still_open = db.scalars(
        select(AuditFinding).where(AuditFinding.site_id == site.id, AuditFinding.resolved_at.is_(None))
    ).all()
    for finding in still_open:
        finding.resolved_at = now

    rows = [
        AuditFinding(
            site_id=site.id,
            page=f["page"],
            severity=Severity(f["severity"]),
            description=f["description"],
        )
        for f in summarized
    ]
    db.add_all(rows)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows
