from datetime import datetime

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Site(Base):
    """A managed site. Single-site mode = exactly one row here.
    Every other module table FKs to site_id (see docs/DECISIONS.md #6)."""

    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), unique=True)
    name: Mapped[str] = mapped_column(String(255))

    # Structured profile produced by Module 1's site-analysis step:
    # {"business_summary": str, "target_audience": str, "existing_topics": [str],
    #  "tone": str, "content_gaps": [str]}
    profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Comma-separated subreddit names (no "r/"), e.g. "SaaS,Entrepreneur".
    # Module 5 monitors these against this site's approved keywords.
    subreddits: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
