from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.reddit_opportunity import RedditOpportunity
from app.schemas.reddit import RedditOpportunityRead, RedditOpportunityStatusUpdate

router = APIRouter(prefix="/api/reddit-opportunities", tags=["reddit"])

# Read/update only for now. Module 5 (PRAW monitoring + draft-reply
# generation) is not built yet — see build order in the project brief.
# Status updates are wired up already since "mark as replied/skipped" is
# pure human-in-the-loop bookkeeping, independent of the monitor pipeline.


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
