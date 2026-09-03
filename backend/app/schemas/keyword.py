from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.keyword import KeywordStatus


class KeywordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    keyword: str
    rationale: str | None
    volume: int | None
    difficulty: float | None
    relevance_score: float | None
    opportunity_score: float | None
    status: KeywordStatus
    created_at: datetime


class KeywordStatusUpdate(BaseModel):
    status: KeywordStatus


class RunKeywordResearchRequest(BaseModel):
    site_id: int
