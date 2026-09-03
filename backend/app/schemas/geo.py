from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.geo_mention import GeoProvider


class GeoMentionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    query: str
    provider: GeoProvider
    mentioned: bool
    context_snippet: str | None
    competitors_mentioned: list | None
    checked_at: datetime
