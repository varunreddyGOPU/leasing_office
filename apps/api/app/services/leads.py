"""Lead upsert with dedupe on email+phone — shared by the estimate tool,
contact form, and (Phase 3) the chatbot extractor."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


def upsert_lead(db: Session, *, email: str | None = None, phone: str | None = None,
                source: str = "form", **fields) -> models.Lead:
    email = email.strip().lower() if email else None
    phone = phone.strip() if phone else None

    lead = None
    if email and phone:
        lead = db.scalar(
            select(models.Lead).where(models.Lead.email == email, models.Lead.phone == phone)
        )
    if lead is None and email:
        lead = db.scalar(select(models.Lead).where(models.Lead.email == email))
    if lead is None and phone:
        lead = db.scalar(select(models.Lead).where(models.Lead.phone == phone))

    if lead is None:
        lead = models.Lead(email=email, phone=phone, source=source)
        db.add(lead)
    else:
        # Fill in whichever contact field we just learned.
        if email and not lead.email:
            lead.email = email
        if phone and not lead.phone:
            lead.phone = phone

    for key, value in fields.items():
        if value is not None:
            setattr(lead, key, value)

    db.flush()
    return lead
