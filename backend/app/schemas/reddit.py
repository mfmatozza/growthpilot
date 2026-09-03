from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.reddit_opportunity import RedditOpportunityStatus


class RedditOpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    thread_url: str
    subreddit: str
    matched_keyword: str
    draft_reply: str | None
    status: RedditOpportunityStatus
    created_at: datetime


class RedditOpportunityStatusUpdate(BaseModel):
    status: RedditOpportunityStatus


class RunRedditMonitorRequest(BaseModel):
    site_id: int
