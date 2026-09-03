from app.services.crawler.site_crawler import discover_key_page_urls, extract_page_content

SAMPLE_HTML = """
<html>
<head>
  <title>Acme Widgets — Home</title>
  <meta name="description" content="We make the best widgets.">
</head>
<body>
  <nav><a href="/ignored-nav-link">Nav</a></nav>
  <h1>Widgets for everyone</h1>
  <h2>Why Acme</h2>
  <h2>Our process</h2>
  <h3>Step one</h3>
  <p>Acme has been making widgets since 2001. Our widgets are the best.</p>
  <footer><a href="/ignored-footer-link">Footer</a></footer>
</body>
</html>
"""

HOMEPAGE_WITH_LINKS = """
<html><body>
  <a href="/pricing">Pricing</a>
  <a href="/blog/post-1">Blog post</a>
  <a href="/random-page">Random</a>
  <a href="https://external.com/thing">External</a>
  <a href="/">Home (self)</a>
  <a href="/pricing">Pricing again</a>
</body></html>
"""


def test_extract_page_content_pulls_headings_and_meta():
    page = extract_page_content("https://acme.com", SAMPLE_HTML)

    assert page.title == "Acme Widgets — Home"
    assert page.meta_description == "We make the best widgets."
    assert page.h1 == ["Widgets for everyone"]
    assert page.h2 == ["Why Acme", "Our process"]
    assert page.h3 == ["Step one"]


def test_extract_page_content_strips_nav_and_footer_from_text():
    page = extract_page_content("https://acme.com", SAMPLE_HTML)

    assert "Nav" not in page.text_excerpt
    assert "Footer" not in page.text_excerpt
    assert "Acme has been making widgets since 2001" in page.text_excerpt


def test_discover_key_page_urls_prioritizes_hinted_paths_and_dedupes():
    urls = discover_key_page_urls("https://acme.com", HOMEPAGE_WITH_LINKS, max_pages=8)

    assert urls[0] == "https://acme.com/pricing"
    assert urls.count("https://acme.com/pricing") == 1  # deduped
    assert "https://external.com/thing" not in urls
    assert "https://acme.com" not in urls  # self-link excluded


def test_discover_key_page_urls_respects_max_pages():
    html = "".join(f'<a href="/page-{i}">p{i}</a>' for i in range(20))
    urls = discover_key_page_urls("https://acme.com", html, max_pages=5)

    assert len(urls) == 5
