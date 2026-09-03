from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.article import Article
from app.schemas.article import ArticleRead

router = APIRouter(prefix="/api/articles", tags=["articles"])

# Read-only for now. Module 2's generation pipeline (SERP research, outline,
# section drafting, internal linking, fact-check pass) is not built yet —
# see build order in the project brief. This gives the dashboard's Articles
# tab something real to call in the meantime.


@router.get("", response_model=list[ArticleRead])
def list_articles(site_id: int | None = None, db: Session = Depends(get_db)) -> list[Article]:
    stmt = select(Article).order_by(Article.created_at.desc())
    if site_id is not None:
        stmt = stmt.where(Article.site_id == site_id)
    return list(db.scalars(stmt).all())
