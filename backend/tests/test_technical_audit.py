from unittest.mock import patch

from app.models.audit_finding import AuditFinding, Severity
from app.pipelines.technical_audit import build_summary_prompt, parse_summary_findings, run_technical_audit
from app.services.audit.pagespeed import PageSpeedError
from app.services.crawler.base import FetchedPage, PageFetcher
from app.services.llm.fake_client import FakeLLMClient

HOMEPAGE_HTML = "<html><head><title>Acme</title></head><body><img src='/x.png'></body></html>"


class FakeFetcher(PageFetcher):
    def fetch(self, url: str) -> FetchedPage:
        return FetchedPage(url=url, status_code=200, html=HOMEPAGE_HTML)


def test_parse_summary_findings_defaults_invalid_severity():
    raw = {"findings": [{"page": "https://acme.com", "severity": "apocalyptic", "description": "bad"}]}
    result = parse_summary_findings(raw, fallback_page="https://acme.com")
    assert result[0]["severity"] == "medium"


def test_parse_summary_findings_drops_empty_description():
    raw = {"findings": [{"page": "https://acme.com", "severity": "high", "description": "  "}]}
    assert parse_summary_findings(raw, fallback_page="https://acme.com") == []


def test_parse_summary_findings_uses_fallback_page_when_missing():
    raw = {"findings": [{"severity": "low", "description": "something"}]}
    result = parse_summary_findings(raw, fallback_page="https://acme.com")
    assert result[0]["page"] == "https://acme.com"


def test_build_summary_prompt_includes_pagespeed_when_present():
    prompt = build_summary_prompt(
        [{"category": "missing_title", "page": "https://acme.com", "description": "no title"}],
        {"scores": {"seo": 80}, "opportunities": [{"title": "Reduce JS", "description": "..."}]},
    )
    assert "no title" in prompt
    assert "seo: 80" in prompt
    assert "Reduce JS" in prompt


def test_build_summary_prompt_omits_pagespeed_section_when_absent():
    prompt = build_summary_prompt([{"category": "x", "page": "p", "description": "d"}], None)
    assert "PageSpeed" not in prompt


@patch("app.pipelines.technical_audit.fetch_pagespeed_report")
def test_run_technical_audit_persists_findings_and_resolves_old_ones(mock_pagespeed, db_session, site):
    mock_pagespeed.return_value = {
        "lighthouseResult": {"categories": {"performance": {"score": 0.5}}, "audits": {}}
    }
    stale = AuditFinding(site_id=site.id, page=site.url, severity=Severity.high, description="old issue")
    db_session.add(stale)
    db_session.commit()

    llm = FakeLLMClient(
        json_response={"findings": [{"page": site.url, "severity": "high", "description": "Missing title tag."}]}
    )

    rows = run_technical_audit(db=db_session, site=site, fetcher=FakeFetcher(), llm=llm)

    db_session.refresh(stale)
    assert stale.resolved_at is not None  # old open finding got resolved by the fresh run
    assert len(rows) == 1
    assert rows[0].severity == Severity.high


@patch("app.pipelines.technical_audit.fetch_pagespeed_report")
def test_run_technical_audit_degrades_gracefully_without_pagespeed(mock_pagespeed, db_session, site):
    mock_pagespeed.side_effect = PageSpeedError("quota exceeded")
    llm = FakeLLMClient(json_response={"findings": [{"page": site.url, "severity": "low", "description": "minor issue"}]})

    rows = run_technical_audit(db=db_session, site=site, fetcher=FakeFetcher(), llm=llm)

    assert len(rows) == 1  # crawl-based findings still produced despite PageSpeed failing


@patch("app.pipelines.technical_audit.fetch_pagespeed_report")
def test_run_technical_audit_no_findings_skips_llm_call(mock_pagespeed, db_session, site):
    mock_pagespeed.side_effect = PageSpeedError("quota exceeded")

    class CleanFetcher(PageFetcher):
        def fetch(self, url):
            return FetchedPage(
                url=url,
                status_code=200,
                html="<html><head><title>Fine</title><meta name='description' content='fine'></head><body></body></html>",
            )

    llm = FakeLLMClient()
    rows = run_technical_audit(db=db_session, site=site, fetcher=CleanFetcher(), llm=llm)

    assert rows == []
    assert llm.calls == []  # nothing to summarize — never called the LLM
