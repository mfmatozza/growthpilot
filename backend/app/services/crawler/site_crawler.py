"""Module 1 step 1: crawl a handful of key pages on a site and extract
structured content from each. Kept pure/testable — `extract_page_content`
and `discover_key_page_urls` take HTML/links in and return plain dataclasses
out, with no network calls, so they're unit-testable without a fetcher."""

import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.crawler.base import FetchError, PageFetcher

# Path fragments that make a link worth prioritizing when picking which
# pages to crawl beyond the homepage. Ordered as a soft priority hint, not
# a strict filter — anything not matching these is still eligible as filler.
_PRIORITY_PATH_HINTS = (
    "product",
    "service",
    "pricing",
    "about",
    "blog",
    "resources",
    "solutions",
    "features",
)


@dataclass
class PageContent:
    url: str
    title: str
    meta_description: str
    h1: list[str] = field(default_factory=list)
    h2: list[str] = field(default_factory=list)
    h3: list[str] = field(default_factory=list)
    text_excerpt: str = ""  # first ~2000 chars of visible body text


def extract_page_content(url: str, html: str) -> PageContent:
    soup = BeautifulSoup(html, "lxml")

    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    meta_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_tag.get("content", "").strip() if meta_tag else ""

    h1 = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2 = [h.get_text(strip=True) for h in soup.find_all("h2")]
    h3 = [h.get_text(strip=True) for h in soup.find_all("h3")]

    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()

    return PageContent(
        url=url,
        title=title,
        meta_description=meta_description,
        h1=h1,
        h2=h2,
        h3=h3,
        text_excerpt=text[:2000],
    )


def discover_key_page_urls(base_url: str, homepage_html: str, max_pages: int = 8) -> list[str]:
    """Pick internal links from the homepage worth crawling as "key pages":
    product/service/pricing/about/blog first, then fill remaining slots with
    other internal links, deduplicated, homepage excluded (caller already
    has it)."""
    soup = BeautifulSoup(homepage_html, "lxml")
    base_domain = urlparse(base_url).netloc

    seen: set[str] = set()
    prioritized: list[str] = []
    other: list[str] = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.netloc != base_domain:
            continue
        normalized = parsed._replace(fragment="", query="").geturl().rstrip("/")
        if not normalized or normalized == base_url.rstrip("/") or normalized in seen:
            continue
        seen.add(normalized)

        if any(hint in normalized.lower() for hint in _PRIORITY_PATH_HINTS):
            prioritized.append(normalized)
        else:
            other.append(normalized)

    return (prioritized + other)[:max_pages]


def crawl_site(base_url: str, fetcher: PageFetcher, max_pages: int = 8) -> list[PageContent]:
    """Fetch the homepage plus up to `max_pages` key internal pages. A page
    that fails to fetch is skipped, not fatal — a partial site profile beats
    no profile at all."""
    pages: list[PageContent] = []

    try:
        homepage = fetcher.fetch(base_url)
    except FetchError:
        return pages

    pages.append(extract_page_content(homepage.url, homepage.html))

    for url in discover_key_page_urls(base_url, homepage.html, max_pages=max_pages):
        try:
            fetched = fetcher.fetch(url)
        except FetchError:
            continue
        pages.append(extract_page_content(fetched.url, fetched.html))

    return pages
