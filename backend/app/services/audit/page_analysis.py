"""Module 3 crawl-based checks: missing titles/meta descriptions, images
without alt text, duplicate titles across the crawled set, and broken
internal links. Extraction and finding-generation are pure functions —
no network calls — so they're unit-testable without a fetcher; only
`crawl_for_audit` and `check_links` touch the network.
"""

from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.crawler.base import FetchError, PageFetcher
from app.services.crawler.site_crawler import discover_key_page_urls


@dataclass
class PageAuditInfo:
    url: str
    title: str
    meta_description: str
    h1_count: int
    images_missing_alt: int
    internal_links: list[str] = field(default_factory=list)


def extract_audit_info(url: str, html: str) -> PageAuditInfo:
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(url).netloc

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_tag.get("content", "").strip() if meta_tag else ""

    images_missing_alt = sum(1 for img in soup.find_all("img") if not img.get("alt", "").strip())

    internal_links: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        absolute = urljoin(url, a["href"])
        parsed = urlparse(absolute)
        if parsed.netloc != base_domain:
            continue
        normalized = parsed._replace(fragment="").geturl()
        if normalized not in seen:
            seen.add(normalized)
            internal_links.append(normalized)

    return PageAuditInfo(
        url=url,
        title=title,
        meta_description=meta_description,
        h1_count=len(soup.find_all("h1")),
        images_missing_alt=images_missing_alt,
        internal_links=internal_links,
    )


def find_missing_title(pages: list[PageAuditInfo]) -> list[dict]:
    return [{"page": p.url, "category": "missing_title", "description": "Page has no <title> tag."} for p in pages if not p.title]


def find_missing_meta_description(pages: list[PageAuditInfo]) -> list[dict]:
    return [
        {"page": p.url, "category": "missing_meta_description", "description": "Page has no meta description."}
        for p in pages
        if not p.meta_description
    ]


def find_missing_alt_text(pages: list[PageAuditInfo]) -> list[dict]:
    return [
        {
            "page": p.url,
            "category": "missing_alt_text",
            "description": f"{p.images_missing_alt} image(s) on this page have no alt text.",
        }
        for p in pages
        if p.images_missing_alt > 0
    ]


def find_duplicate_titles(pages: list[PageAuditInfo]) -> list[dict]:
    titles: dict[str, list[str]] = {}
    for p in pages:
        if p.title:
            titles.setdefault(p.title, []).append(p.url)

    findings = []
    for title, urls in titles.items():
        if len(urls) > 1:
            for url in urls:
                findings.append(
                    {
                        "page": url,
                        "category": "duplicate_title",
                        "description": f'Title "{title}" is duplicated across {len(urls)} pages: {", ".join(urls)}.',
                    }
                )
    return findings


def find_broken_links(pages: list[PageAuditInfo], link_statuses: dict[str, int | None]) -> list[dict]:
    """link_statuses maps a URL to its HTTP status code, or None if the
    request itself failed (DNS error, timeout, etc — treated as broken). A
    link *absent* from the dict was never checked (check_links caps how many
    it fetches per run) and must NOT be treated as broken — that would flag
    every link past the cap as broken, which is wrong, not just imprecise."""
    findings = []
    for p in pages:
        for link in p.internal_links:
            if link not in link_statuses:
                continue
            status = link_statuses[link]
            if status is None or status >= 400:
                findings.append(
                    {
                        "page": p.url,
                        "category": "broken_link",
                        "description": f"Links to {link}, which returned {status if status else 'no response'}.",
                    }
                )
    return findings


def run_all_checks(pages: list[PageAuditInfo], link_statuses: dict[str, int | None]) -> list[dict]:
    return [
        *find_missing_title(pages),
        *find_missing_meta_description(pages),
        *find_missing_alt_text(pages),
        *find_duplicate_titles(pages),
        *find_broken_links(pages, link_statuses),
    ]


def crawl_for_audit(base_url: str, fetcher: PageFetcher, max_pages: int = 8) -> list[PageAuditInfo]:
    pages: list[PageAuditInfo] = []
    try:
        homepage = fetcher.fetch(base_url)
    except FetchError:
        return pages
    pages.append(extract_audit_info(homepage.url, homepage.html))

    for url in discover_key_page_urls(base_url, homepage.html, max_pages=max_pages):
        try:
            fetched = fetcher.fetch(url)
        except FetchError:
            continue
        pages.append(extract_audit_info(fetched.url, fetched.html))

    return pages


def check_links(urls: list[str], fetcher: PageFetcher, limit: int = 60) -> dict[str, int | None]:
    """Capped at `limit` links per run — a synchronous request-per-run
    pipeline shouldn't fan out to hundreds of HEAD-equivalent fetches.
    Links beyond the cap are simply absent from the result and must be
    treated as "not checked", not "broken" — see find_broken_links."""
    statuses: dict[str, int | None] = {}
    for url in urls[:limit]:
        try:
            statuses[url] = fetcher.fetch(url).status_code
        except FetchError:
            statuses[url] = None
    return statuses
