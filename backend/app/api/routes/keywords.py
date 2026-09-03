from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.keyword import Keyword
from app.models.site import Site
from app.pipelines.keyword_research import run_keyword_research
from app.schemas.keyword import KeywordRead, KeywordStatusUpdate, RunKeywordResearchRequest
from app.services.crawler.httpx_fetcher import HttpxFetcher
from app.services.keyword_data.base import KeywordDataError
from app.services.keyword_data.dataforseo import DataForSEOProvider
from app.services.llm.anthropic_client import AnthropicClient
from app.services.llm.base import LLMError

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.get("", response_model=list[KeywordRead])
def list_keywords(site_id: int | None = None, status: str | None = None, db: Session = Depends(get_db)) -> list[Keyword]:
    stmt = select(Keyword).order_by(Keyword.opportunity_score.desc().nullslast())
    if site_id is not None:
        stmt = stmt.where(Keyword.site_id == site_id)
    if status is not None:
        stmt = stmt.where(Keyword.status == status)
    return list(db.scalars(stmt).all())


@router.patch("/{keyword_id}", response_model=KeywordRead)
def update_keyword_status(keyword_id: int, payload: KeywordStatusUpdate, db: Session = Depends(get_db)) -> Keyword:
    keyword = db.get(Keyword, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    keyword.status = payload.status
    db.commit()
    db.refresh(keyword)
    return keyword


@router.post("/research", response_model=list[KeywordRead], status_code=201)
def trigger_keyword_research(payload: RunKeywordResearchRequest, db: Session = Depends(get_db)) -> list[Keyword]:
    """Runs the Module 1 pipeline synchronously. Fine for a single-user
    internal tool with one site; move behind the scheduler/job queue if this
    starts blocking the request for too long once DataForSEO + a slower
    Claude call are both in the loop."""
    site = db.get(Site, payload.site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    try:
        llm = AnthropicClient()
    except LLMError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    keyword_data_provider = None
    try:
        keyword_data_provider = DataForSEOProvider()
    except KeywordDataError:
        # Enrichment is optional — candidates still get generated and stored
        # with null volume/difficulty, reviewable once DataForSEO is configured.
        pass

    return run_keyword_research(
        db=db,
        site=site,
        fetcher=HttpxFetcher(),
        llm=llm,
        keyword_data_provider=keyword_data_provider,
    )
