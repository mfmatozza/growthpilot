from app.models.geo_mention import GeoProvider
from app.models.keyword import Keyword, KeywordStatus
from app.pipelines.geo_tracker import (
    get_available_providers,
    parse_mention_analysis,
    run_geo_check,
    select_target_queries,
)
from app.services.llm.fake_client import FakeLLMClient


def test_parse_mention_analysis_defaults_missing_fields():
    result = parse_mention_analysis({})
    assert result == {"mentioned": False, "context_snippet": None, "competitors": []}


def test_parse_mention_analysis_empty_snippet_becomes_none():
    result = parse_mention_analysis({"mentioned": True, "context_snippet": "   "})
    assert result["context_snippet"] is None


def test_parse_mention_analysis_drops_falsy_competitors():
    result = parse_mention_analysis({"competitors": ["Acme", "", None, "Widgetco"]})
    assert result["competitors"] == ["Acme", "Widgetco"]


def test_select_target_queries_only_approved_ordered_by_opportunity(db_session, site):
    db_session.add_all(
        [
            Keyword(site_id=site.id, keyword="low", status=KeywordStatus.approved, opportunity_score=10),
            Keyword(site_id=site.id, keyword="high", status=KeywordStatus.approved, opportunity_score=90),
            Keyword(site_id=site.id, keyword="candidate", status=KeywordStatus.candidate, opportunity_score=99),
        ]
    )
    db_session.commit()

    queries = select_target_queries(db_session, site, limit=10)

    assert queries == ["high", "low"]  # candidate excluded, ordered by score desc


def test_select_target_queries_respects_limit(db_session, site):
    db_session.add_all(
        [Keyword(site_id=site.id, keyword=f"kw{i}", status=KeywordStatus.approved, opportunity_score=i) for i in range(5)]
    )
    db_session.commit()

    assert len(select_target_queries(db_session, site, limit=2)) == 2


def test_get_available_providers_skips_unconfigured(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    get_settings.cache_clear()

    providers = get_available_providers()

    assert set(providers.keys()) == {GeoProvider.chatgpt}
    get_settings.cache_clear()


def test_run_geo_check_persists_mentions_for_each_query_and_provider(db_session, site):
    db_session.add(Keyword(site_id=site.id, keyword="best widget supplier", status=KeywordStatus.approved, opportunity_score=80))
    db_session.commit()

    answer_llm = FakeLLMClient(text_response="Acme is a great choice for widgets.")
    analysis_llm = FakeLLMClient(json_response={"mentioned": True, "context_snippet": "Acme is a great choice", "competitors": ["Widgetco"]})

    rows = run_geo_check(
        db=db_session,
        site=site,
        providers={GeoProvider.chatgpt: answer_llm, GeoProvider.claude: answer_llm},
        analysis_llm=analysis_llm,
    )

    assert len(rows) == 2
    assert {r.provider for r in rows} == {GeoProvider.chatgpt, GeoProvider.claude}
    assert all(r.mentioned for r in rows)
    assert all(r.competitors_mentioned == ["Widgetco"] for r in rows)


def test_run_geo_check_skips_failing_provider_without_crashing(db_session, site):
    from app.services.llm.base import LLMClient, LLMError

    class BrokenLLM(LLMClient):
        def complete_json(self, **kwargs):
            raise LLMError("boom")

        def complete_text(self, **kwargs):
            raise LLMError("boom")

    db_session.add(Keyword(site_id=site.id, keyword="widget guide", status=KeywordStatus.approved, opportunity_score=50))
    db_session.commit()

    rows = run_geo_check(
        db=db_session,
        site=site,
        providers={GeoProvider.chatgpt: BrokenLLM()},
        analysis_llm=FakeLLMClient(),
    )

    assert rows == []


def test_run_geo_check_no_queries_returns_empty(db_session, site):
    rows = run_geo_check(
        db=db_session,
        site=site,
        providers={GeoProvider.chatgpt: FakeLLMClient(text_response="x")},
        analysis_llm=FakeLLMClient(json_response={"mentioned": False}),
    )
    assert rows == []
