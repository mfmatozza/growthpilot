import pytest

from app.services.audit.page_analysis import (
    crawl_for_audit,
    extract_audit_info,
    find_broken_links,
    find_duplicate_titles,
    find_missing_alt_text,
    find_missing_meta_description,
    find_missing_title,
)
from app.services.crawler.base import FetchError, PageFetcher

NO_TITLE_HTML = "<html><body><p>hi</p></body></html>"

WITH_ISSUES_HTML = """
<html>
<head><title>Acme</title></head>
<body>
  <img src="/a.png" alt="">
  <img src="/b.png" alt="a real description">
  <img src="/c.png">
  <a href="/page-1">one</a>
  <a href="https://acme.com/page-2">two</a>
  <a href="https://external.com/thing">external</a>
</body>
</html>
"""


def test_extract_audit_info_counts_missing_alt_and_internal_links():
    info = extract_audit_info("https://acme.com", WITH_ISSUES_HTML)

    assert info.title == "Acme"
    assert info.images_missing_alt == 2  # empty alt and no alt attr at all
    assert "https://acme.com/page-1" in info.internal_links
    assert "https://acme.com/page-2" in info.internal_links
    assert "https://external.com/thing" not in info.internal_links


def test_find_missing_title_flags_pages_without_one():
    info = extract_audit_info("https://acme.com", NO_TITLE_HTML)
    findings = find_missing_title([info])
    assert len(findings) == 1
    assert findings[0]["page"] == "https://acme.com"


def test_find_missing_title_ignores_pages_with_one():
    info = extract_audit_info("https://acme.com", WITH_ISSUES_HTML)
    assert find_missing_title([info]) == []


def test_find_missing_meta_description():
    info = extract_audit_info("https://acme.com", WITH_ISSUES_HTML)
    findings = find_missing_meta_description([info])
    assert len(findings) == 1


def test_find_missing_alt_text_only_flags_pages_with_issues():
    with_issue = extract_audit_info("https://acme.com/a", WITH_ISSUES_HTML)
    clean_html = '<html><head><title>Clean</title></head><body><img src="/x.png" alt="fine"></body></html>'
    clean = extract_audit_info("https://acme.com/b", clean_html)

    findings = find_missing_alt_text([with_issue, clean])

    assert len(findings) == 1
    assert findings[0]["page"] == "https://acme.com/a"
    assert "2 image" in findings[0]["description"]


def test_find_duplicate_titles():
    a = extract_audit_info("https://acme.com/a", '<html><head><title>Same</title></head><body></body></html>')
    b = extract_audit_info("https://acme.com/b", '<html><head><title>Same</title></head><body></body></html>')
    c = extract_audit_info("https://acme.com/c", '<html><head><title>Different</title></head><body></body></html>')

    findings = find_duplicate_titles([a, b, c])

    assert len(findings) == 2
    assert {f["page"] for f in findings} == {"https://acme.com/a", "https://acme.com/b"}


def test_find_broken_links_flags_4xx_5xx_and_no_response():
    info = extract_audit_info("https://acme.com", WITH_ISSUES_HTML)
    statuses = {"https://acme.com/page-1": 404, "https://acme.com/page-2": 200}

    findings = find_broken_links([info], statuses)

    assert len(findings) == 1
    assert "page-1" in findings[0]["description"]


def test_find_broken_links_ignores_links_never_checked():
    # check_links caps how many links it fetches per run — a link absent
    # from link_statuses was never checked, not evidence it's broken.
    info = extract_audit_info("https://acme.com", WITH_ISSUES_HTML)
    findings = find_broken_links([info], {})

    assert findings == []


def test_find_broken_links_flags_explicit_none_as_failed_request():
    # None (present in the dict) means check_links tried and the request
    # itself failed — that IS evidence of brokenness, unlike "absent".
    info = extract_audit_info("https://acme.com", WITH_ISSUES_HTML)
    findings = find_broken_links([info], {"https://acme.com/page-1": None, "https://acme.com/page-2": 200})

    assert len(findings) == 1
    assert "page-1" in findings[0]["description"]


def test_crawl_for_audit_raises_when_homepage_is_unreachable():
    class AlwaysFailsFetcher(PageFetcher):
        def fetch(self, url: str):
            raise FetchError("DNS resolution failed")

    with pytest.raises(FetchError):
        crawl_for_audit("https://broken.example", AlwaysFailsFetcher())
