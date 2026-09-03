from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.geo_mention import GeoMention
from app.models.site import Site
from app.pipelines.geo_tracker import get_available_providers, run_geo_check
from app.schemas.geo import GeoMentionRead, RunGeoCheckRequest
from app.services.llm.base import LLMError
from app.services.llm.factory import get_default_llm_client

router = APIRouter(prefix="/api/geo-mentions", tags=["geo"])


@router.get("", response_model=list[GeoMentionRead])
def list_mentions(site_id: int | None = None, db: Session = Depends(get_db)) -> list[GeoMention]:
    stmt = select(GeoMention).order_by(GeoMention.checked_at.desc())
    if site_id is not None:
        stmt = stmt.where(GeoMention.site_id == site_id)
    return list(db.scalars(stmt).all())


@router.post("/run", response_model=list[GeoMentionRead], status_code=201)
def trigger_geo_check(payload: RunGeoCheckRequest, db: Session = Depends(get_db)) -> list[GeoMention]:
    """Runs synchronously, same tradeoff as /api/keywords/research — fine
    for a single-user tool with a handful of approved keywords per site."""
    site = db.get(Site, payload.site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    providers = get_available_providers()
    if not providers:
        raise HTTPException(
            status_code=400,
            detail="No GEO provider has an API key configured (need at least one of "
            "OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_GEMINI_API_KEY, PERPLEXITY_API_KEY).",
        )

    try:
        analysis_llm = get_default_llm_client()
    except LLMError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return run_geo_check(db=db, site=site, providers=providers, analysis_llm=analysis_llm)
