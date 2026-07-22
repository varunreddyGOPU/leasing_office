"""Resident portal: lease view, one-click renewal, maintenance requests."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.db import get_db
from app.routers.auth import get_current_resident
from app.services.alerts import queue_alert
from app.services.renewals import (
    accept_renewal,
    decline_renewal,
    ensure_renewal_offer,
    get_active_lease,
    get_upcoming_lease,
)

router = APIRouter(prefix="/api/me", tags=["portal"])

MAINTENANCE_CATEGORIES = {"plumbing", "electrical", "appliance", "hvac", "pest", "other"}
ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTOS = 5
MAX_PHOTO_BYTES = 5 * 1024 * 1024


def _lease_out(db: Session, lease: models.Lease) -> schemas.LeaseOut:
    plan = lease.unit.floor_plan
    return schemas.LeaseOut(
        id=lease.id,
        start_date=lease.start_date,
        end_date=lease.end_date,
        days_to_end=(lease.end_date - date.today()).days,
        monthly_rent=float(lease.monthly_rent),
        auto_renew_opt_in=lease.auto_renew_opt_in,
        renewal_status=lease.renewal_status,
        renewal_offer_rent=(
            float(lease.renewal_offer_rent) if lease.renewal_offer_rent is not None else None
        ),
        unit=schemas.LeaseUnitInfo(
            unit_number=lease.unit.unit_number,
            floor_plan_name=plan.name,
            bedrooms=plan.bedrooms,
            bathrooms=float(plan.bathrooms),
            sqft=plan.sqft,
        ),
    )


@router.get("/lease", response_model=schemas.MeLeaseResponse)
def my_lease(
    resident: models.Resident = Depends(get_current_resident),
    db: Session = Depends(get_db),
) -> schemas.MeLeaseResponse:
    lease = get_active_lease(db, resident.id)
    if lease is not None:
        ensure_renewal_offer(db, lease)
        db.commit()
    upcoming = get_upcoming_lease(db, resident.id)
    return schemas.MeLeaseResponse(
        resident=schemas.ResidentOut.model_validate(resident),
        lease=_lease_out(db, lease) if lease else None,
        upcoming_lease=_lease_out(db, upcoming) if upcoming else None,
    )


@router.post("/renewal", response_model=schemas.MeLeaseResponse)
def renewal_action(
    payload: schemas.RenewalActionIn,
    resident: models.Resident = Depends(get_current_resident),
    db: Session = Depends(get_db),
) -> schemas.MeLeaseResponse:
    lease = get_active_lease(db, resident.id)
    if lease is None:
        raise HTTPException(status_code=404, detail="No active lease found.")
    if lease.renewal_status != "offered" or lease.renewal_offer_rent is None:
        raise HTTPException(
            status_code=409,
            detail=f"No open renewal offer (status: {lease.renewal_status}).",
        )
    if payload.action == "accept":
        accept_renewal(db, lease)
    else:
        decline_renewal(db, lease)
    db.commit()
    upcoming = get_upcoming_lease(db, resident.id)
    return schemas.MeLeaseResponse(
        resident=schemas.ResidentOut.model_validate(resident),
        lease=_lease_out(db, lease),
        upcoming_lease=_lease_out(db, upcoming) if upcoming else None,
    )


def _ticket_out(ticket: models.MaintenanceTicket) -> schemas.MaintenanceTicketOut:
    return schemas.MaintenanceTicketOut(
        id=ticket.id,
        category=ticket.category,
        description=ticket.description,
        status=ticket.status,
        created_at=ticket.created_at,
        resolved_at=ticket.resolved_at,
        photo_count=len(ticket.photos or []),
    )


@router.get("/maintenance", response_model=list[schemas.MaintenanceTicketOut])
def my_tickets(
    resident: models.Resident = Depends(get_current_resident),
    db: Session = Depends(get_db),
) -> list[schemas.MaintenanceTicketOut]:
    tickets = db.scalars(
        select(models.MaintenanceTicket)
        .where(models.MaintenanceTicket.resident_id == resident.id)
        .order_by(models.MaintenanceTicket.created_at.desc())
    ).all()
    return [_ticket_out(t) for t in tickets]


@router.post("/maintenance", response_model=schemas.MaintenanceCreateResult)
async def create_ticket(
    category: str = Form(...),
    description: str = Form(..., min_length=5, max_length=4000),
    photos: list[UploadFile] = File(default=[]),
    resident: models.Resident = Depends(get_current_resident),
    db: Session = Depends(get_db),
) -> schemas.MaintenanceCreateResult:
    if category not in MAINTENANCE_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"Category must be one of: {', '.join(sorted(MAINTENANCE_CATEGORIES))}",
        )
    lease = get_active_lease(db, resident.id)
    if lease is None:
        raise HTTPException(status_code=404, detail="No active lease found.")
    # Browsers submit an empty file part when the picker is left untouched.
    photos = [p for p in photos if p.filename]
    if len(photos) > MAX_PHOTOS:
        raise HTTPException(status_code=422, detail=f"At most {MAX_PHOTOS} photos.")

    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for photo in photos:
        if photo.content_type not in ALLOWED_PHOTO_TYPES:
            raise HTTPException(status_code=422, detail="Photos must be JPEG, PNG, or WebP.")
        data = await photo.read()
        if len(data) > MAX_PHOTO_BYTES:
            raise HTTPException(status_code=422, detail="Each photo must be under 5 MB.")
        ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[
            photo.content_type
        ]
        name = f"{uuid.uuid4().hex}{ext}"
        (upload_root / name).write_bytes(data)
        saved.append(name)

    ticket = models.MaintenanceTicket(
        unit_id=lease.unit_id,
        resident_id=resident.id,
        category=category,
        description=description,
        photos=saved,
        status="new",
    )
    db.add(ticket)
    db.flush()
    queue_alert(
        db,
        type="maintenance_created",
        recipient_type="office",
        recipient_id=0,
        payload={
            "ticket_id": ticket.id,
            "unit_number": lease.unit.unit_number,
            "category": category,
        },
    )
    db.commit()
    return schemas.MaintenanceCreateResult(id=ticket.id, status=ticket.status)


@router.get("/maintenance/{ticket_id}/photos/{index}")
def ticket_photo(
    ticket_id: int,
    index: int,
    resident: models.Resident = Depends(get_current_resident),
    db: Session = Depends(get_db),
) -> FileResponse:
    ticket = db.get(models.MaintenanceTicket, ticket_id)
    if ticket is None or ticket.resident_id != resident.id:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    photos = ticket.photos or []
    if not 0 <= index < len(photos):
        raise HTTPException(status_code=404, detail="Photo not found.")
    path = Path(settings.upload_dir) / photos[index]
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Photo not found.")
    return FileResponse(path)
