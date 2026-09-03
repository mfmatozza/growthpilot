from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.reddit_opportunity import RedditOpportunity
from app.models.site import Site
from app.pipelines.reddit_monitor import run_reddit_monitor
from app.schemas.reddit import RedditOpportunityRead, RedditOpportunityStatusUpdate, RunRedditMonitorRequest
from app.services.llm.base import LLMError
from app.services.llm.factory import get_default_llm_client
from app.services.reddit.base import RedditError
from app.services.reddit.praw_client import PrawRedditClient

router = APIRouter(prefix="/api/reddit-opportunities", tags=["reddit"])


@router.get("", response_model=list[RedditOpportunityRead])
def list_opportunities(site_id: int | None = None, db: Session = Depends(get_db)) -> list[RedditOpportunity]:
    stmt = select(RedditOpportunity).order_by(RedditOpportunity.created_at.desc())
    if site_id is not None:
        stmt = stmt.where(RedditOpportunity.site_id == site_id)
    return list(db.scalars(stmt).all())


@router.patch("/{opportunity_id}", response_model=RedditOpportunityRead)
def update_status(
    opportunity_id: int, payload: RedditOpportunityStatusUpdate, db: Session = Depends(get_db)
) -> RedditOpportunity:
    opportunity = db.get(RedditOpportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    opportunity.status = payload.status
    db.commit()
    db.refresh(opportunity)
    return opportunity


@router.post("/run", response_model=list[RedditOpportunityRead], status_code=201)
def trigger_reddit_monitor(payload: RunRedditMonitorRequest, db: Session = Depends(get_db)) -> list[RedditOpportunity]:
    site = db.get(Site, payload.site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if not site.subreddits:
        raise HTTPException(
            status_code=400,
            detail="No subreddits configured for this site — set them first (PATCH /api/sites/{id}).",
        )

    try:
        reddit_client = PrawRedditClient()
    except RedditError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        llm = get_default_llm_client()
    except LLMError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return run_reddit_monitor(db=db, site=site, reddit_client=reddit_client, llm=llm)
