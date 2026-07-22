"""Office endpoints (maintenance kanban). Gated by X-Admin-Key for now;
full role-based admin auth arrives with the Phase 5 dashboard."""
from __future__ import annotations

import hmac
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.db import get_db
from app.services.alerts import queue_alert

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(x_admin_key: str = Header(default="")) -> None:
    if not hmac.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="Admin key required.")


@router.get(
    "/maintenance",
    response_model=list[schemas.AdminMaintenanceTicketOut],
    dependencies=[Depends(require_admin)],
)
def all_tickets(db: Session = Depends(get_db)) -> list[schemas.AdminMaintenanceTicketOut]:
    rows = db.execute(
        select(models.MaintenanceTicket, models.Unit, models.Resident)
        .join(models.Unit, models.MaintenanceTicket.unit_id == models.Unit.id)
        .join(models.Resident, models.MaintenanceTicket.resident_id == models.Resident.id)
        .order_by(models.MaintenanceTicket.created_at.desc())
    ).all()
    return [
        schemas.AdminMaintenanceTicketOut(
            id=ticket.id,
            category=ticket.category,
            description=ticket.description,
            status=ticket.status,
            created_at=ticket.created_at,
            resolved_at=ticket.resolved_at,
            photo_count=len(ticket.photos or []),
            unit_number=unit.unit_number,
            resident_name=resident.name,
            resident_id=resident.id,
        )
        for ticket, unit, resident in rows
    ]


@router.post(
    "/maintenance/{ticket_id}/status",
    response_model=schemas.AdminMaintenanceTicketOut,
    dependencies=[Depends(require_admin)],
)
def set_status(
    ticket_id: int, payload: schemas.MaintenanceStatusIn, db: Session = Depends(get_db)
) -> schemas.AdminMaintenanceTicketOut:
    ticket = db.get(models.MaintenanceTicket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    if payload.status == ticket.status:
        raise HTTPException(status_code=409, detail="Ticket already has that status.")

    ticket.status = payload.status
    ticket.resolved_at = (
        datetime.now(timezone.utc) if payload.status == "resolved" else None
    )
    queue_alert(
        db,
        type="maintenance_status",
        recipient_type="resident",
        recipient_id=ticket.resident_id,
        payload={"ticket_id": ticket.id, "status": payload.status, "category": ticket.category},
    )
    db.commit()

    unit = db.get(models.Unit, ticket.unit_id)
    resident = db.get(models.Resident, ticket.resident_id)
    return schemas.AdminMaintenanceTicketOut(
        id=ticket.id,
        category=ticket.category,
        description=ticket.description,
        status=ticket.status,
        created_at=ticket.created_at,
        resolved_at=ticket.resolved_at,
        photo_count=len(ticket.photos or []),
        unit_number=unit.unit_number,
        resident_name=resident.name,
        resident_id=resident.id,
    )
