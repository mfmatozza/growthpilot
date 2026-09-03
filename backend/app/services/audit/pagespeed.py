"""Google PageSpeed Insights v5 — works keyless at low volume (a key just
raises the rate limit), so this is the Lighthouse-equivalent that needs no
paid API, matching the project's usage-based-only constraint.
"""

import httpx

from app.services.retry import external_api_retry

_RETRYABLE = (httpx.TransportError, httpx.TimeoutException)
_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


class PageSpeedError(Exception):
    pass


@external_api_retry(_RETRYABLE)
def fetch_pagespeed_report(url: str, api_key: str = "") -> dict:
    params = {"url": url, "category": ["PERFORMANCE", "ACCESSIBILITY", "SEO"], "strategy": "mobile"}
    if api_key:
        params["key"] = api_key
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(_API_URL, params=params)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise PageSpeedError(f"PageSpeed Insights request failed: {exc}") from exc

    return response.json()


def summarize_pagespeed_report(report: dict) -> dict:
    """Pulls out just what the LLM summarization step needs: category
    scores (0-100) and the audits PSI itself flagged as opportunities
    (score < 0.9), each with its own plain-ish description."""
    categories = report.get("lighthouseResult", {}).get("categories", {})
    scores = {name: round((data.get("score") or 0) * 100) for name, data in categories.items()}

    audits = report.get("lighthouseResult", {}).get("audits", {})
    opportunities = [
        {"id": audit_id, "title": audit.get("title", audit_id), "description": audit.get("description", "")}
        for audit_id, audit in audits.items()
        if audit.get("score") is not None and audit["score"] < 0.9 and audit.get("scoreDisplayMode") != "informative"
    ]

    return {"scores": scores, "opportunities": opportunities[:15]}
