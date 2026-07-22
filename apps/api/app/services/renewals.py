"""Renewal offers: offer = min(current market asking rent, current rent x cap).
Phase 5's nightly analytics will also write offers at T-95; this on-demand path
keeps the portal functional from day one and uses identical rules."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.services.alerts import queue_alert

DEFAULT_CAP_PCT = 0.05
DEFAULT_OFFER_DAYS = 95
RENEWAL_TERM_MONTHS = 12


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _renewal_rules(db: Session) -> dict:
    rule = db.scalar(select(models.PricingRule).where(models.PricingRule.key == "renewal"))
    value = rule.value_json if rule else {}
    return {
        "cap_pct": float(value.get("cap_pct", DEFAULT_CAP_PCT)),
        "offer_days_before_end": int(value.get("offer_days_before_end", DEFAULT_OFFER_DAYS)),
    }


def get_active_lease(db: Session, resident_id: int) -> models.Lease | None:
    today = date.today()
    return db.scalar(
        select(models.Lease)
        .where(
            models.Lease.resident_id == resident_id,
            models.Lease.start_date <= today,
            models.Lease.end_date >= today,
        )
        .order_by(models.Lease.end_date.desc())
    )


def get_upcoming_lease(db: Session, resident_id: int) -> models.Lease | None:
    today = date.today()
    return db.scalar(
        select(models.Lease)
        .where(models.Lease.resident_id == resident_id, models.Lease.start_date > today)
        .order_by(models.Lease.start_date)
    )


def market_asking_rent(db: Session, floor_plan_id: int) -> Decimal | None:
    rent = db.scalar(
        select(models.PriceHistory.asking_rent)
        .where(
            models.PriceHistory.floor_plan_id == floor_plan_id,
            models.PriceHistory.source == "internal",
        )
        .order_by(models.PriceHistory.effective_date.desc())
        .limit(1)
    )
    return _money(rent) if rent is not None else None


def ensure_renewal_offer(db: Session, lease: models.Lease) -> None:
    """Compute and persist an offer once the lease enters the renewal window."""
    if lease.renewal_status != "none":
        return
    rules = _renewal_rules(db)
    days_to_end = (lease.end_date - date.today()).days
    if days_to_end < 0 or days_to_end > rules["offer_days_before_end"]:
        return

    cap = _money(Decimal(str(lease.monthly_rent)) * Decimal(str(1 + rules["cap_pct"])))
    asking = market_asking_rent(db, lease.unit.floor_plan_id)
    offer = min(asking, cap) if asking is not None else cap

    lease.renewal_offer_rent = offer
    lease.renewal_status = "offered"
    queue_alert(
        db,
        type="renewal_offer",
        recipient_type="resident",
        recipient_id=lease.resident_id,
        payload={
            "lease_id": lease.id,
            "current_rent": float(lease.monthly_rent),
            "offer_rent": float(offer),
            "lease_end": lease.end_date.isoformat(),
        },
    )


def accept_renewal(db: Session, lease: models.Lease) -> models.Lease:
    new_start = lease.end_date + timedelta(days=1)
    month_index = new_start.year * 12 + (new_start.month - 1) + RENEWAL_TERM_MONTHS
    new_end = date(month_index // 12, month_index % 12 + 1, min(new_start.day, 28)) - timedelta(
        days=1
    )
    renewal = models.Lease(
        unit_id=lease.unit_id,
        resident_id=lease.resident_id,
        start_date=new_start,
        end_date=new_end,
        monthly_rent=lease.renewal_offer_rent,
        auto_renew_opt_in=lease.auto_renew_opt_in,
        renewal_status="none",
    )
    db.add(renewal)
    lease.renewal_status = "accepted"
    # Unit stays occupied; clear any vacancy flag.
    lease.unit.available_date = None
    queue_alert(
        db,
        type="renewal_confirmed",
        recipient_type="resident",
        recipient_id=lease.resident_id,
        payload={
            "lease_id": lease.id,
            "new_rent": float(lease.renewal_offer_rent),
            "new_start": new_start.isoformat(),
            "new_end": new_end.isoformat(),
        },
    )
    return renewal


def decline_renewal(db: Session, lease: models.Lease) -> None:
    lease.renewal_status = "declined"
    # Feed the availability pipeline: unit becomes leasable the day after
    # the current lease ends.
    lease.unit.status = "available"
    lease.unit.available_date = lease.end_date + timedelta(days=1)
    queue_alert(
        db,
        type="renewal_declined",
        recipient_type="office",
        recipient_id=0,
        payload={
            "lease_id": lease.id,
            "unit_number": lease.unit.unit_number,
            "lease_end": lease.end_date.isoformat(),
        },
    )
