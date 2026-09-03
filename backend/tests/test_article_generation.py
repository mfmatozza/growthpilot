from app.models.article import ArticleStatus, ArticleType
from app.models.keyword import Keyword, KeywordStatus
from app.pipelines.article_generation import (
    build_outline_prompt,
    draft_article_body,
    insert_internal_links,
    parse_outline,
    run_generate_article,
    slugify,
    strip_em_dashes,
)
from app.services.crawler.base import FetchedPage, PageFetcher
from app.services.llm.fake_client import FakeLLMClient
from app.services.serp.base import SerpError, SerpProvider
from tests.conftest import RoutedLLM


def test_slugify_basic():
    assert slugify("How To Fix A Widget!") == "how-to-fix-a-widget"


def test_slugify_collapses_and_strips():
    assert slugify("  --Multiple   Spaces--  ") == "multiple-spaces"


def test_slugify_empty_falls_back():
    assert slugify("???") == "article"


def test_strip_em_dashes_removes_spaced_and_unspaced():
    assert strip_em_dashes("A — B") == "A, B"
    assert strip_em_dashes("A—B") == "A, B"
    assert strip_em_dashes("A – B") == "A, B"


def test_strip_em_dashes_leaves_normal_text_alone():
    assert strip_em_dashes("A normal sentence, with a comma.") == "A normal sentence, with a comma."


def test_parse_outline_drops_sections_without_heading():
    raw = {"title": "T", "sections": [{"key_points": ["x"]}, {"heading": "Real", "key_points": ["y"]}]}
    outline = parse_outline(raw)
    assert len(outline["sections"]) == 1
    assert outline["sections"][0]["heading"] == "Real"


def test_parse_outline_defaults_missing_fields():
    outline = parse_outline({})
    assert outline == {"title": "", "sections": [], "differentiation_angle": ""}


def test_build_outline_prompt_notes_missing_competitor_data():
    prompt = build_outline_prompt("widget guide", {"business_summary": "widgets"}, [])
    assert "No live competitor data available" in prompt


def test_build_outline_prompt_includes_competitor_headings():
    from app.services.crawler.site_crawler import PageContent

    page = PageContent(url="https://x.com", title="Top guide", meta_description="", h2=["Step 1", "Step 2"])
    prompt = build_outline_prompt("widget guide", {}, [page])
    assert "Step 1" in prompt
    assert "Top guide" in prompt


def test_draft_article_body_includes_title_and_all_sections():
    llm = FakeLLMClient(text_response="Section content here.")
    outline = {"title": "Widget Guide", "sections": [{"heading": "Intro", "key_points": []}, {"heading": "Details", "key_points": []}]}

    body = draft_article_body("widget guide", outline, llm)

    assert body.startswith("# Widget Guide")
    assert "## Intro" in body
    assert "## Details" in body
    assert body.count("Section content here.") == 2


def test_insert_internal_links_returns_unchanged_body_with_no_candidates():
    assert insert_internal_links("some body", [], FakeLLMClient()) == "some body"


def test_insert_internal_links_uses_llm_output():
    llm = FakeLLMClient(json_response={"body_markdown": "some body with [a link](/other-post)"})
    result = insert_internal_links("some body", [("Other Post", "other-post")], llm)
    assert result == "some body with [a link](/other-post)"


def test_insert_internal_links_falls_back_to_original_on_empty_response():
    llm = FakeLLMClient(json_response={})
    result = insert_internal_links("original body", [("Other", "other")], llm)
    assert result == "original body"


class FakeFetcher(PageFetcher):
    def fetch(self, url: str) -> FetchedPage:
        return FetchedPage(url=url, status_code=200, html="<html><head><title>Competitor</title></head><body></body></html>")


def test_run_generate_article_end_to_end_without_serp_provider(db_session, site):
    keyword = Keyword(site_id=site.id, keyword="widget buying guide", status=KeywordStatus.approved, opportunity_score=80)
    db_session.add(keyword)
    db_session.commit()
    db_session.refresh(keyword)

    outline_llm = FakeLLMClient(
        json_response={
            "title": "The Widget Buying Guide",
            "sections": [{"heading": "What to look for", "key_points": ["durability"]}],
            "differentiation_angle": "practical checklist",
        }
    )
    section_llm = FakeLLMClient(text_response="Look for durable — materials.")  # deliberate em dash to test stripping

    article = run_generate_article(
        db=db_session,
        site=site,
        keyword=keyword,
        llm=RoutedLLM(outline_llm, section_llm),
        fetcher=FakeFetcher(),
        serp_provider=None,
    )

    assert article.status == ArticleStatus.draft
    assert article.title == "The Widget Buying Guide"
    assert article.slug == "the-widget-buying-guide"
    assert article.keyword_id == keyword.id
    assert "—" not in article.body_markdown  # strip_em_dashes actually applied end-to-end
    assert "## What to look for" in article.body_markdown


def test_run_generate_article_skips_serp_when_provider_fails(db_session, site):
    class BrokenSerp(SerpProvider):
        def top_results(self, query, num_results=8):
            raise SerpError("no budget")

    keyword = Keyword(site_id=site.id, keyword="widget guide", status=KeywordStatus.approved, opportunity_score=80)
    db_session.add(keyword)
    db_session.commit()
    db_session.refresh(keyword)

    outline_llm = FakeLLMClient(json_response={"title": "T", "sections": [{"heading": "H", "key_points": []}]})
    section_llm = FakeLLMClient(text_response="body")

    article = run_generate_article(
        db=db_session,
        site=site,
        keyword=keyword,
        llm=RoutedLLM(outline_llm, section_llm),
        fetcher=FakeFetcher(),
        serp_provider=BrokenSerp(),
    )

    assert article.status == ArticleStatus.draft  # didn't blow up despite SERP failing


def test_run_generate_article_comparison_type_is_stored(db_session, site):
    keyword = Keyword(site_id=site.id, keyword="widget vs gadget", status=KeywordStatus.approved, opportunity_score=80)
    db_session.add(keyword)
    db_session.commit()
    db_session.refresh(keyword)

    outline_llm = FakeLLMClient(json_response={"title": "Widget vs Gadget", "sections": [{"heading": "H", "key_points": []}]})
    section_llm = FakeLLMClient(text_response="body")

    article = run_generate_article(
        db=db_session,
        site=site,
        keyword=keyword,
        llm=RoutedLLM(outline_llm, section_llm),
        fetcher=FakeFetcher(),
        article_type=ArticleType.comparison,
    )

    assert article.article_type == ArticleType.comparison
