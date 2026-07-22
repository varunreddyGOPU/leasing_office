"""Alert outbox writes. Phase 6's sender worker delivers these via
SendGrid/Twilio; until then rows accumulate as 'pending'."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app import models


def queue_alert(
    db: Session,
    *,
    type: str,
    recipient_type: str,
    recipient_id: int,
    payload: dict,
) -> models.Alert:
    alert = models.Alert(
        type=type,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        payload_json=payload,
        send_after=datetime.now(timezone.utc),
        status="pending",
        attempts=0,
    )
    db.add(alert)
    return alert
