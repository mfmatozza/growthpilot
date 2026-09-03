from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class SiteCreate(BaseModel):
    url: str
    name: str

    @field_validator("url", "name")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        # A trailing space in a URL isn't cosmetic — it fails DNS resolution
        # outright, which silently broke the crawler (confirmed against a
        # real stored site: the crawl failed entirely and the audit
        # pipeline mis-reported that as "no issues found").
        return value.strip()


class SiteUpdate(BaseModel):
    url: str | None = None
    name: str | None = None

    @field_validator("url", "name")
    @classmethod
    def strip_whitespace(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class SiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    name: str
    profile: dict | None
    created_at: datetime
