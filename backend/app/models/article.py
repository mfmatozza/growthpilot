import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ArticleStatus(str, enum.Enum):
    draft = "draft"
    review = "review"
    published = "published"


class ArticleType(str, enum.Enum):
    how_to = "how_to"
    informational = "informational"
    comparison = "comparison"


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(512))
    slug: Mapped[str] = mapped_column(String(512))
    article_type: Mapped[ArticleType] = mapped_column(
        Enum(ArticleType, native_enum=False), default=ArticleType.informational
    )

    outline: Mapped[dict | None] = mapped_column(Text, nullable=True)  # JSON-encoded outline
    body_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus, native_enum=False), default=ArticleStatus.draft
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
