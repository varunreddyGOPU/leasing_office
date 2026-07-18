from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db

router = APIRouter(prefix="/api", tags=["news"])

COVERED_ZIPS = {"48326", "48307", "48309", "48342"}


@router.get("/news", response_model=list[schemas.NewsItemOut])
def list_news(
    zip: str | None = Query(None, max_length=10),
    db: Session = Depends(get_db),
) -> list[schemas.NewsItemOut]:
    stmt = (
        select(models.NewsItem)
        .where(models.NewsItem.hidden.is_(False))
        .order_by(models.NewsItem.pinned.desc(), models.NewsItem.published_at.desc())
        .limit(50)
    )
    if zip and zip in COVERED_ZIPS:
        stmt = stmt.where(models.NewsItem.zip == zip)
    return [schemas.NewsItemOut.model_validate(row) for row in db.scalars(stmt).all()]
