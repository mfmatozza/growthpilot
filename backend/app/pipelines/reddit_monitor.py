"""Module 5: search a site's configured subreddits for its top approved
keywords, and draft (never post) a reply for each new matching thread.

Posting is always a human action — see app/models/reddit_opportunity.py's
status field and the brief's explicit "never auto-post" requirement. This
pipeline only ever reads from Reddit and writes rows for a human to review.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.keyword import Keyword, KeywordStatus
from app.models.reddit_opportunity import RedditOpportunity, RedditOpportunityStatus
from app.models.site import Site
from app.services.llm.base import LLMClient, LLMError
from app.services.reddit.base import RedditError, RedditMonitorClient, RedditThread

logger = logging.getLogger(__name__)

_DRAFT_REPLY_SYSTEM = (
    "You draft a helpful, non-promotional Reddit reply to a thread relevant to a business. Respond only "
    'via the emit_result tool call with this exact JSON shape: {"draft_reply": string}. Write like a '
    "genuine community member sharing knowledge, never like an ad. Only mention the business/product if "
    "it's genuinely the most helpful answer to what the thread is asking, and if you do, disclose the "
    "affiliation plainly. If there's nothing genuinely useful to add, the draft_reply can say so — a human "
    "reviews every draft before anything is posted, so an honest 'skip this one' is better than filler."
)


def select_target_keywords(db: Session, site: Site, limit: int = 10) -> list[str]:
    """Same intent as Module 4's target-query selection (top approved
    keywords by opportunity score) — kept as its own copy rather than a
    shared import so this pipeline stays independently testable, per the
    brief's modularity requirement."""
    stmt = (
        select(Keyword)
        .where(Keyword.site_id == site.id, Keyword.status == KeywordStatus.approved)
        .order_by(Keyword.opportunity_score.desc().nullslast())
        .limit(limit)
    )
    return [k.keyword for k in db.scalars(stmt).all()]


def build_draft_reply_prompt(site: Site, thread: RedditThread, matched_keyword: str) -> str:
    return (
        f"Business: {site.name} ({site.url})\n"
        f"Matched keyword: {matched_keyword}\n"
        f"Subreddit: r/{thread.subreddit}\n"
        f"Thread title: {thread.title}\n"
        f"Thread body: {thread.body[:1500]}"
    )


def parse_draft_reply(raw: dict) -> str:
    return str(raw.get("draft_reply", "")).strip()


def generate_draft_reply(site: Site, thread: RedditThread, matched_keyword: str, llm: LLMClient) -> str:
    raw = llm.complete_json(system=_DRAFT_REPLY_SYSTEM, user=build_draft_reply_prompt(site, thread, matched_keyword))
    return parse_draft_reply(raw)


def run_reddit_monitor(
    *,
    db: Session,
    site: Site,
    reddit_client: RedditMonitorClient,
    llm: LLMClient,
    max_keywords: int = 10,
    results_per_keyword: int = 5,
) -> list[RedditOpportunity]:
    if not site.subreddits:
        return []
    subreddits = [s.strip() for s in site.subreddits.split(",") if s.strip()]
    if not subreddits:
        return []

    keywords = select_target_keywords(db, site, limit=max_keywords)
    existing_urls = {
        o.thread_url
        for o in db.scalars(select(RedditOpportunity).where(RedditOpportunity.site_id == site.id)).all()
    }

    rows: list[RedditOpportunity] = []
    for subreddit in subreddits:
        for keyword in keywords:
            try:
                threads = reddit_client.search(subreddit, keyword, limit=results_per_keyword)
            except RedditError as exc:
                logger.warning("Reddit search failed for r/%s / %r: %s", subreddit, keyword, exc)
                continue

            for thread in threads:
                if thread.url in existing_urls:
                    continue
                existing_urls.add(thread.url)

                try:
                    draft = generate_draft_reply(site, thread, keyword, llm)
                except LLMError as exc:
                    logger.warning("Draft reply generation failed for %s: %s", thread.url, exc)
                    draft = None

                row = RedditOpportunity(
                    site_id=site.id,
                    thread_url=thread.url,
                    subreddit=subreddit,
                    matched_keyword=keyword,
                    draft_reply=draft,
                    status=RedditOpportunityStatus.new,
                )
                db.add(row)
                rows.append(row)

    db.commit()
    for row in rows:
        db.refresh(row)
    return rows
