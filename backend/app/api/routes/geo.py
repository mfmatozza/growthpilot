from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.geo_mention import GeoMention
from app.schemas.geo import GeoMentionRead

router = APIRouter(prefix="/api/geo-mentions", tags=["geo"])

# Read-only for now. Module 4 (ChatGPT/Claude/Gemini/Perplexity querying +
# mention parsing) is not built yet — see build order in the project brief.


@router.get("", response_model=list[GeoMentionRead])
def list_mentions(site_id: int | None = None, db: Session = Depends(get_db)) -> list[GeoMention]:
    stmt = select(GeoMention).order_by(GeoMention.checked_at.desc())
    if site_id is not None:
        stmt = stmt.where(GeoMention.site_id == site_id)
    return list(db.scalars(stmt).all())
