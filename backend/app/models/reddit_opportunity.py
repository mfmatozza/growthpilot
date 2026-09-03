import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RedditOpportunityStatus(str, enum.Enum):
    new = "new"
    replied = "replied"
    skipped = "skipped"


class RedditOpportunity(Base):
    __tablename__ = "reddit_opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))

    thread_url: Mapped[str] = mapped_column(String(2048))
    subreddit: Mapped[str] = mapped_column(String(255))
    matched_keyword: Mapped[str] = mapped_column(String(512))
    draft_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RedditOpportunityStatus] = mapped_column(
        Enum(RedditOpportunityStatus, native_enum=False), default=RedditOpportunityStatus.new
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
