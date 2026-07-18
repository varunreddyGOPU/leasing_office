from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.ratelimit import rate_limit
from app.services.leads import upsert_lead

router = APIRouter(prefix="/api", tags=["leads"])


@router.post(
    "/leads",
    response_model=schemas.LeadOut,
    dependencies=[Depends(rate_limit("leads", per_minute=10))],
)
def create_lead(payload: schemas.LeadCreate, db: Session = Depends(get_db)) -> schemas.LeadOut:
    notes_parts = []
    if payload.preferred_tour_at:
        notes_parts.append(f"Tour requested: {payload.preferred_tour_at:%A %b %d, %I:%M %p}")
    if payload.notes:
        notes_parts.append(payload.notes)

    lead = upsert_lead(
        db,
        email=payload.email,
        phone=payload.phone,
        source="form",
        name=payload.name,
        desired_bedrooms=payload.desired_bedrooms,
        notes=" | ".join(notes_parts) or None,
    )
    db.commit()
    return schemas.LeadOut(
        id=lead.id,
        status="received",
        message="Thanks! The office will reach out during business hours (Mon–Fri 9:30–5).",
    )
