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


class ArticleDetailRead(ArticleRead):
    outline: dict | None
    body_markdown: str | None


class GenerateArticleRequest(BaseModel):
    site_id: int
    keyword_id: int
    article_type: ArticleType = ArticleType.informational


class ArticleStatusUpdate(BaseModel):
    status: ArticleStatus
