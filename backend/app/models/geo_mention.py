import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GeoProvider(str, enum.Enum):
    chatgpt = "chatgpt"
    claude = "claude"
    gemini = "gemini"
    perplexity = "perplexity"


class GeoMention(Base):
    __tablename__ = "geo_mentions"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))

    query: Mapped[str] = mapped_column(String(512))
    provider: Mapped[GeoProvider] = mapped_column(Enum(GeoProvider, native_enum=False))
    mentioned: Mapped[bool] = mapped_column(Boolean)
    context_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    competitors_mentioned: Mapped[list | None] = mapped_column(JSON, nullable=True)

    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
