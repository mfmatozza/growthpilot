from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.article import Article
from app.models.keyword import Keyword
from app.models.site import Site
from app.pipelines.article_generation import run_generate_article
from app.schemas.article import ArticleDetailRead, ArticleRead, ArticleStatusUpdate, GenerateArticleRequest
from app.services.crawler.httpx_fetcher import HttpxFetcher
from app.services.llm.base import LLMError
from app.services.llm.factory import get_default_llm_client
from app.services.serp.base import SerpError
from app.services.serp.serpapi import SerpApiProvider

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("", response_model=list[ArticleRead])
def list_articles(site_id: int | None = None, db: Session = Depends(get_db)) -> list[Article]:
    stmt = select(Article).order_by(Article.created_at.desc())
    if site_id is not None:
        stmt = stmt.where(Article.site_id == site_id)
    return list(db.scalars(stmt).all())


@router.get("/{article_id}", response_model=ArticleDetailRead)
def get_article(article_id: int, db: Session = Depends(get_db)) -> Article:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.patch("/{article_id}", response_model=ArticleRead)
def update_article_status(article_id: int, payload: ArticleStatusUpdate, db: Session = Depends(get_db)) -> Article:
    """The only mutation exposed on purpose — nothing here auto-publishes
    anywhere outside this app; this just tracks where a draft is in your
    own review process (draft -> review -> published)."""
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article.status = payload.status
    db.commit()
    db.refresh(article)
    return article


@router.post("/generate", response_model=ArticleDetailRead, status_code=201)
def trigger_article_generation(payload: GenerateArticleRequest, db: Session = Depends(get_db)) -> Article:
    """Runs synchronously — an outline call plus one LLM call per outline
    section (5-8 sections) can take a while; same tradeoff as the other
    /run-style endpoints, more pronounced here."""
    site = db.get(Site, payload.site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    keyword = db.get(Keyword, payload.keyword_id)
    if not keyword or keyword.site_id != site.id:
        raise HTTPException(status_code=404, detail="Keyword not found for this site")

    try:
        llm = get_default_llm_client()
    except LLMError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    serp_provider = None
    try:
        serp_provider = SerpApiProvider()
    except SerpError:
        pass  # optional — outline generation works without live competitor data, see decisions doc #25

    return run_generate_article(
        db=db,
        site=site,
        keyword=keyword,
        llm=llm,
        fetcher=HttpxFetcher(),
        serp_provider=serp_provider,
        article_type=payload.article_type,
    )
