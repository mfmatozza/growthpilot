from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.site import Site
from app.schemas.site import SiteCreate, SiteRead, SiteUpdate

router = APIRouter(prefix="/api/sites", tags=["sites"])


@router.get("", response_model=list[SiteRead])
def list_sites(db: Session = Depends(get_db)) -> list[Site]:
    return list(db.scalars(select(Site)).all())


@router.post("", response_model=SiteRead, status_code=201)
def create_site(payload: SiteCreate, db: Session = Depends(get_db)) -> Site:
    existing = db.scalar(select(Site).where(Site.url == payload.url))
    if existing:
        raise HTTPException(status_code=409, detail="Site with this URL already exists")
    site = Site(url=payload.url, name=payload.name)
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.get("/{site_id}", response_model=SiteRead)
def get_site(site_id: int, db: Session = Depends(get_db)) -> Site:
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.patch("/{site_id}", response_model=SiteRead)
def update_site(site_id: int, payload: SiteUpdate, db: Session = Depends(get_db)) -> Site:
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if payload.url is not None:
        site.url = payload.url
    if payload.name is not None:
        site.name = payload.name
    if payload.subreddits is not None:
        site.subreddits = payload.subreddits
    db.commit()
    db.refresh(site)
    return site


@router.delete("/{site_id}", status_code=204)
def delete_site(site_id: int, db: Session = Depends(get_db)) -> None:
    """Cascades to that site's keywords/articles/audit findings/GEO
    mentions/Reddit opportunities — every FK to sites.id is ondelete=CASCADE
    (see app/models/*)."""
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    db.delete(site)
    db.commit()
