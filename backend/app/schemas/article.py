from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.article import ArticleStatus, ArticleType


class ArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    keyword_id: int | None
    title: str
    slug: str
    article_type: ArticleType
    status: ArticleStatus
    created_at: datetime
