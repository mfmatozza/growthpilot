from app.models.keyword import KeywordStatus
from app.pipelines.keyword_research import (
    generate_keyword_candidates,
    parse_keyword_candidates,
    parse_site_profile,
    run_keyword_research,
)
from app.services.crawler.base import FetchedPage, PageFetcher
from app.services.keyword_data.fake_provider import FakeKeywordDataProvider
from app.services.llm.fake_client import FakeLLMClient
from tests.conftest import SequencedLLM


class FakeFetcher(PageFetcher):
    """Always returns the same minimal homepage — enough for the pipeline
    to run end-to-end without hitting the network."""

    def fetch(self, url: str) -> FetchedPage:
        return FetchedPage(url=url, status_code=200, html="<html><head><title>Acme</title></head><body></body></html>")


def test_parse_site_profile_fills_defaults_for_missing_keys():
    profile = parse_site_profile({"business_summary": "Sells widgets"})

    assert profile["business_summary"] == "Sells widgets"
    assert profile["target_audience"] == ""
    assert profile["existing_topics"] == []
    assert profile["content_gaps"] == []


def test_parse_site_profile_coerces_non_string_list_items():
    profile = parse_site_profile({"existing_topics": ["seo", 123, ""]})

    assert profile["existing_topics"] == ["seo", "123"]  # empty string dropped, non-str coerced


def test_parse_keyword_candidates_dedupes_case_insensitively():
    raw = {
        "keywords": [
            {"keyword": "best widgets", "rationale": "r1", "relevance_score": 80},
            {"keyword": "Best Widgets", "rationale": "r2", "relevance_score": 90},
        ]
    }
    candidates = parse_keyword_candidates(raw)

    assert len(candidates) == 1
    assert candidates[0]["keyword"] == "best widgets"


def test_parse_keyword_candidates_drops_entries_without_a_keyword():
    raw = {"keywords": [{"rationale": "no keyword here", "relevance_score": 50}]}
    assert parse_keyword_candidates(raw) == []


def test_parse_keyword_candidates_clamps_relevance_score():
    raw = {"keywords": [{"keyword": "widgets", "relevance_score": 150}]}
    assert parse_keyword_candidates(raw)[0]["relevance_score"] == 100.0


def test_parse_keyword_candidates_handles_non_numeric_relevance_score():
    raw = {"keywords": [{"keyword": "widgets", "relevance_score": "not a number"}]}
    assert parse_keyword_candidates(raw)[0]["relevance_score"] == 0.0


def test_generate_keyword_candidates_uses_llm_client():
    llm = FakeLLMClient(
        json_response={"keywords": [{"keyword": "widget care guide", "rationale": "r", "relevance_score": 70}]}
    )
    candidates = generate_keyword_candidates({"business_summary": "widgets"}, llm)

    assert candidates == [{"keyword": "widget care guide", "rationale": "r", "relevance_score": 70.0}]
    assert llm.calls[0]["kind"] == "json"


def test_run_keyword_research_persists_candidates_with_scores(db_session, site):
    # run_keyword_research calls complete_json twice (profile, then
    # candidates) with different expected shapes, so a sequencing wrapper
    # feeds each call its own canned FakeLLMClient response in order.
    profile_llm = FakeLLMClient(json_response={"business_summary": "Acme sells widgets", "target_audience": "DIYers"})
    candidates_llm = FakeLLMClient(
        json_response={
            "keywords": [
                {"keyword": "how to fix a widget", "rationale": "high intent", "relevance_score": 85},
                {"keyword": "widget history", "rationale": "low intent", "relevance_score": 20},
            ]
        }
    )
    provider = FakeKeywordDataProvider({"how to fix a widget": (5000, 30.0), "widget history": (50, 80.0)})

    rows = run_keyword_research(
        db=db_session,
        site=site,
        fetcher=FakeFetcher(),
        llm=SequencedLLM(profile_llm, candidates_llm),
        keyword_data_provider=provider,
    )

    assert len(rows) == 2
    assert all(r.status == KeywordStatus.candidate for r in rows)
    high_intent = next(r for r in rows if r.keyword == "how to fix a widget")
    low_intent = next(r for r in rows if r.keyword == "widget history")
    assert high_intent.volume == 5000
    assert high_intent.opportunity_score > low_intent.opportunity_score
    assert site.profile["business_summary"] == "Acme sells widgets"


def test_run_keyword_research_without_keyword_data_provider_stores_null_metrics(db_session, site):
    profile_llm = FakeLLMClient(json_response={"business_summary": "Acme sells widgets"})
    candidates_llm = FakeLLMClient(
        json_response={"keywords": [{"keyword": "widget basics", "rationale": "r", "relevance_score": 50}]}
    )

    rows = run_keyword_research(
        db=db_session,
        site=site,
        fetcher=FakeFetcher(),
        llm=SequencedLLM(profile_llm, candidates_llm),
        keyword_data_provider=None,
    )

    assert rows[0].volume is None
    assert rows[0].difficulty is None
    assert rows[0].opportunity_score is not None  # still scored, just without volume/difficulty
