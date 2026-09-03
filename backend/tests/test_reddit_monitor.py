from app.models.keyword import Keyword, KeywordStatus
from app.models.reddit_opportunity import RedditOpportunity, RedditOpportunityStatus
from app.pipelines.reddit_monitor import (
    build_draft_reply_prompt,
    parse_draft_reply,
    run_reddit_monitor,
    select_target_keywords,
)
from app.services.llm.fake_client import FakeLLMClient
from app.services.reddit.base import RedditError, RedditThread
from app.services.reddit.fake_client import FakeRedditClient


def test_parse_draft_reply_defaults_to_empty_string():
    assert parse_draft_reply({}) == ""


def test_parse_draft_reply_strips_whitespace():
    assert parse_draft_reply({"draft_reply": "  hello  "}) == "hello"


def test_build_draft_reply_prompt_includes_thread_and_keyword():
    thread = RedditThread(url="https://reddit.com/r/x/1", subreddit="x", title="Best tool?", body="looking for options")
    prompt = build_draft_reply_prompt(_site_stub(), thread, "widget tool")
    assert "Best tool?" in prompt
    assert "widget tool" in prompt
    assert "r/x" in prompt


def _site_stub():
    from app.models.site import Site

    return Site(id=1, url="https://acme.com", name="Acme")


def test_select_target_keywords_only_approved(db_session, site):
    db_session.add_all(
        [
            Keyword(site_id=site.id, keyword="approved one", status=KeywordStatus.approved, opportunity_score=50),
            Keyword(site_id=site.id, keyword="still candidate", status=KeywordStatus.candidate, opportunity_score=99),
        ]
    )
    db_session.commit()

    assert select_target_keywords(db_session, site) == ["approved one"]


def test_run_reddit_monitor_returns_empty_without_subreddits_configured(db_session, site):
    rows = run_reddit_monitor(db=db_session, site=site, reddit_client=FakeRedditClient(), llm=FakeLLMClient())
    assert rows == []


def test_run_reddit_monitor_creates_opportunities_with_draft_replies(db_session, site):
    site.subreddits = "SaaS, Entrepreneur"
    db_session.add(Keyword(site_id=site.id, keyword="widget tool", status=KeywordStatus.approved, opportunity_score=80))
    db_session.commit()

    thread = RedditThread(url="https://reddit.com/r/SaaS/abc", subreddit="SaaS", title="Need a widget tool", body="help")
    reddit_client = FakeRedditClient({"widget tool": [thread]})
    llm = FakeLLMClient(json_response={"draft_reply": "Here's a genuinely useful answer..."})

    rows = run_reddit_monitor(db=db_session, site=site, reddit_client=reddit_client, llm=llm)

    # The fake returns the same thread regardless of which subreddit is
    # searched — the pipeline correctly dedupes it to one row within the
    # run (see test_run_reddit_monitor_skips_already_recorded_threads for
    # the across-runs case). What matters here is both subreddits got hit.
    assert len(rows) == 1
    assert rows[0].status == RedditOpportunityStatus.new
    assert rows[0].draft_reply == "Here's a genuinely useful answer..."
    assert {c[0] for c in reddit_client.calls} == {"SaaS", "Entrepreneur"}


def test_run_reddit_monitor_skips_already_recorded_threads(db_session, site):
    site.subreddits = "SaaS"
    db_session.add(Keyword(site_id=site.id, keyword="widget tool", status=KeywordStatus.approved, opportunity_score=80))
    db_session.add(
        RedditOpportunity(
            site_id=site.id,
            thread_url="https://reddit.com/r/SaaS/abc",
            subreddit="SaaS",
            matched_keyword="widget tool",
            status=RedditOpportunityStatus.new,
        )
    )
    db_session.commit()

    thread = RedditThread(url="https://reddit.com/r/SaaS/abc", subreddit="SaaS", title="Need a widget tool", body="help")
    reddit_client = FakeRedditClient({"widget tool": [thread]})

    rows = run_reddit_monitor(db=db_session, site=site, reddit_client=reddit_client, llm=FakeLLMClient())

    assert rows == []


def test_run_reddit_monitor_continues_past_a_failing_subreddit(db_session, site):
    site.subreddits = "broken, SaaS"
    db_session.add(Keyword(site_id=site.id, keyword="widget tool", status=KeywordStatus.approved, opportunity_score=80))
    db_session.commit()

    class PartiallyBrokenClient(FakeRedditClient):
        def search(self, subreddit, query, limit=5):
            if subreddit == "broken":
                raise RedditError("banned/private subreddit")
            return super().search(subreddit, query, limit)

    thread = RedditThread(url="https://reddit.com/r/SaaS/abc", subreddit="SaaS", title="t", body="b")
    reddit_client = PartiallyBrokenClient({"widget tool": [thread]})

    rows = run_reddit_monitor(db=db_session, site=site, reddit_client=reddit_client, llm=FakeLLMClient(json_response={"draft_reply": "x"}))

    assert len(rows) == 1
    assert rows[0].subreddit == "SaaS"


def test_run_reddit_monitor_stores_null_draft_on_llm_failure(db_session, site):
    from app.services.llm.base import LLMClient, LLMError

    class BrokenLLM(LLMClient):
        def complete_json(self, **kwargs):
            raise LLMError("boom")

        def complete_text(self, **kwargs):
            raise LLMError("boom")

    site.subreddits = "SaaS"
    db_session.add(Keyword(site_id=site.id, keyword="widget tool", status=KeywordStatus.approved, opportunity_score=80))
    db_session.commit()

    thread = RedditThread(url="https://reddit.com/r/SaaS/abc", subreddit="SaaS", title="t", body="b")
    reddit_client = FakeRedditClient({"widget tool": [thread]})

    rows = run_reddit_monitor(db=db_session, site=site, reddit_client=reddit_client, llm=BrokenLLM())

    assert len(rows) == 1
    assert rows[0].draft_reply is None
