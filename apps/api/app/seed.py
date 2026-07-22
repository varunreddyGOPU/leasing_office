"""Idempotent sample-data seed. Run with: python -m app.seed

Seeds: 3 floor plans, 20 units, 24 months of synthetic price history
(3%/yr trend + summer-peak seasonality + noise), residents + leases for
occupied units with staggered end dates, 5 leads, 2 estimates, 3 news
items, and the pricing_rules config. All values are SAMPLE data meant to
be edited in the admin UI.
"""
from __future__ import annotations

import hashlib
import math
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app import models
from app.db import SessionLocal
from app.security import hash_password

random.seed(48326)

# Sample-resident portal password (dev/demo only — replace flow in production).
DEMO_RESIDENT_PASSWORD = "auburn-demo"

ANNUAL_TREND = 0.03
SEASONAL_AMPLITUDE = 0.03  # +/-3%, peaking in July

FLOOR_PLANS = [
    {
        "name": "The Birch",
        "bedrooms": 1,
        "bathrooms": Decimal("1.0"),
        "sqft": 850,
        "base_rent": Decimal("1295.00"),
        "description": (
            "1 bed / 1 bath townhome, ~850 sqft. Private entry, in-home washer & dryer, "
            "patio or balcony, electric fireplace. Sample pricing — edit in admin."
        ),
    },
    {
        "name": "The Cedar",
        "bedrooms": 2,
        "bathrooms": Decimal("1.5"),
        "sqft": 1100,
        "base_rent": Decimal("1550.00"),
        "description": (
            "2 bed / 1.5 bath townhome, ~1,100 sqft with master suite. Private entry, "
            "in-home washer & dryer, patio or balcony, electric fireplace. Sample pricing."
        ),
    },
    {
        "name": "The Aspen",
        "bedrooms": 3,
        "bathrooms": Decimal("2.0"),
        "sqft": 1350,
        "base_rent": Decimal("1850.00"),
        "description": (
            "3 bed / 2 bath townhome, ~1,350 sqft with master suite. Private entry, "
            "in-home washer & dryer, patio or balcony, electric fireplace. Sample pricing."
        ),
    },
]

# floor plan index -> number of units
UNIT_MIX = [8, 8, 4]

RESIDENT_NAMES = [
    "Avery Sample", "Jordan Example", "Riley Placeholder", "Casey Demo",
    "Morgan Test", "Quinn Sample", "Taylor Example", "Cameron Demo",
    "Skyler Test", "Rowan Sample", "Emerson Example", "Finley Demo",
    "Harper Test", "Sage Sample", "Reese Example", "Dakota Demo",
    "Peyton Test",
]

PRICING_RULES = {
    "term_premiums": {"6": 0.08, "9": 0.04, "12": 0.0, "15": -0.02},
    "seasonality_multipliers": {
        "1": 0.97, "2": 0.97, "3": 0.99, "4": 1.00, "5": 1.02, "6": 1.03,
        "7": 1.03, "8": 1.02, "9": 1.00, "10": 0.99, "11": 0.98, "12": 0.97,
    },
    "pet_policy": {"pet_rent_monthly": 35, "pet_fee_one_time": 250, "max_pets": 2},
    "furnished_premium_monthly": 300,
    "fees": {"application_fee": 50, "security_deposit_months": 1.0},
    "carports": {"included": 1, "extra_monthly": 25},
    "renewal": {"cap_pct": 0.05, "offer_days_before_end": 95},
    "analytics_thresholds": {
        "raise_occupancy_above": 0.95,
        "raise_days_vacant_below": 14,
        "concession_occupancy_below": 0.88,
        "concession_days_vacant_above": 30,
        "max_annual_raise_pct": 0.06,
    },
    "notice": {"rent_increase_notice_days": 30},
}

NEWS_ITEMS = [
    {
        "title": "[SAMPLE] Auburn Hills announces summer concert series at Riverside Park",
        "source": "Seed Data",
        "url": "https://example.com/auburn-hills-concert-series",
        "category": "events",
        "zip": "48326",
    },
    {
        "title": "[SAMPLE] Oakland University opens new engineering building for fall semester",
        "source": "Seed Data",
        "url": "https://example.com/ou-engineering-building",
        "category": "oakland_university",
        "zip": "48309",
    },
    {
        "title": "[SAMPLE] M-59 resurfacing project: lane closures expected through September",
        "source": "Seed Data",
        "url": "https://example.com/m59-resurfacing",
        "category": "roads_transit",
        "zip": "48326",
    },
]


def add_months(d: date, n: int) -> date:
    month_index = d.year * 12 + (d.month - 1) + n
    return date(month_index // 12, month_index % 12 + 1, 1)


def synthetic_rent(base_rent: Decimal, months_ago: int) -> Decimal:
    """Asking rent `months_ago` months back: trend + seasonality + noise, rounded to $5."""
    month = add_months(date.today().replace(day=1), -months_ago)
    trend = (1 + ANNUAL_TREND) ** (-months_ago / 12)
    seasonal = 1 + SEASONAL_AMPLITUDE * math.sin(2 * math.pi * (month.month - 4) / 12)
    noise = random.uniform(-15, 15)
    rent = float(base_rent) * trend * seasonal + noise
    return Decimal(int(round(rent / 5) * 5))


def seed() -> None:
    with SessionLocal() as db:
        if db.scalar(select(models.FloorPlan.id).limit(1)) is not None:
            print("Seed data already present; skipping.")
            return

        today = date.today()

        # --- Floor plans -------------------------------------------------
        plans = [models.FloorPlan(**fp) for fp in FLOOR_PLANS]
        db.add_all(plans)
        db.flush()

        # --- 24 months of price history ----------------------------------
        for plan in plans:
            for months_ago in range(23, -1, -1):
                db.add(
                    models.PriceHistory(
                        floor_plan_id=plan.id,
                        effective_date=add_months(today.replace(day=1), -months_ago),
                        asking_rent=synthetic_rent(plan.base_rent, months_ago),
                        source="internal",
                    )
                )

        # --- 20 units: 17 occupied, 3 available (one per plan) -----------
        units: list[models.Unit] = []
        unit_no = 0
        for plan, count in zip(plans, UNIT_MIX):
            for i in range(count):
                unit_no += 1
                available = i == count - 1  # last unit of each plan is vacant
                units.append(
                    models.Unit(
                        floor_plan_id=plan.id,
                        unit_number=f"2610-{unit_no:02d}",
                        tier="premium" if i % 4 == 0 else "standard",
                        status="available" if available else "occupied",
                        available_date=today + timedelta(days=random.randint(10, 45))
                        if available
                        else None,
                    )
                )
        db.add_all(units)
        db.flush()

        # --- Residents + leases for occupied units -----------------------
        occupied = [u for u in units if u.status == "occupied"]
        plan_by_id = {p.id: p for p in plans}
        for idx, (unit, name) in enumerate(zip(occupied, RESIDENT_NAMES)):
            resident = models.Resident(
                name=name,
                email=f"resident{idx + 1}@example.com",
                phone=f"248-555-{1000 + idx:04d}",
                password_hash=hash_password(DEMO_RESIDENT_PASSWORD),
            )
            db.add(resident)
            db.flush()
            # Stagger lease ends across the next 1–17 months so renewal
            # windows (90/60/30 days) have material to work with on day one.
            end = add_months(today.replace(day=1), idx + 1) + timedelta(
                days=random.randint(0, 27)
            )
            start = end.replace(day=1)
            start = add_months(start, -12) + timedelta(days=end.day - 1)
            base = plan_by_id[unit.floor_plan_id].base_rent
            db.add(
                models.Lease(
                    unit_id=unit.id,
                    resident_id=resident.id,
                    start_date=start,
                    end_date=end,
                    monthly_rent=base - Decimal(random.choice([0, 25, 50, 75])),
                    auto_renew_opt_in=idx % 3 == 0,
                    renewal_status="none",
                )
            )

        # --- Leads -------------------------------------------------------
        leads = [
            models.Lead(
                name="Sam Prospect", email="sam.prospect@example.com", phone="248-555-0201",
                desired_bedrooms=2, move_in_date=today + timedelta(days=40),
                budget=Decimal("1600"), pets="1 cat", source="chatbot", status="new",
            ),
            models.Lead(
                name="Lee Inquiry", email="lee.inquiry@example.com", phone="248-555-0202",
                desired_bedrooms=1, move_in_date=today + timedelta(days=25),
                budget=Decimal("1350"), source="form", status="contacted",
            ),
            models.Lead(
                name="Pat Caller", phone="248-555-0203", desired_bedrooms=3,
                move_in_date=today + timedelta(days=75), budget=Decimal("1900"),
                pets="1 dog", source="phone", status="new",
            ),
            models.Lead(
                name="Jo Student", email="jo.student@example.com", desired_bedrooms=1,
                move_in_date=today + timedelta(days=55), budget=Decimal("1300"),
                notes="Oakland University grad student", source="form", status="toured",
            ),
            models.Lead(
                name="Corp Relo Team", email="relo@example.com", phone="248-555-0205",
                desired_bedrooms=2, move_in_date=today + timedelta(days=30),
                budget=Decimal("2000"), notes="furnished corporate rental",
                source="chatbot", status="new",
            ),
        ]
        db.add_all(leads)
        db.flush()

        # --- A couple of stored estimates --------------------------------
        cedar = plans[1]
        db.add(
            models.Estimate(
                lead_id=leads[0].id,
                floor_plan_id=cedar.id,
                inputs_json={
                    "floor_plan": "The Cedar", "lease_term_months": 12,
                    "move_in_date": str(today + timedelta(days=40)),
                    "pets": [{"type": "cat"}], "carports": 1, "furnished": False,
                },
                breakdown_json={
                    "base_rent": 1550, "term_adjustment": 0, "pet_rent": 35,
                    "furnished_premium": 0,
                },
                monthly_estimate=Decimal("1585.00"),
                move_in_total=Decimal("3435.00"),  # first month + deposit + app fee + pet fee
            )
        )
        birch = plans[0]
        db.add(
            models.Estimate(
                lead_id=leads[1].id,
                floor_plan_id=birch.id,
                inputs_json={
                    "floor_plan": "The Birch", "lease_term_months": 12,
                    "move_in_date": str(today + timedelta(days=25)),
                    "pets": [], "carports": 1, "furnished": False,
                },
                breakdown_json={
                    "base_rent": 1295, "term_adjustment": 0, "pet_rent": 0,
                    "furnished_premium": 0,
                },
                monthly_estimate=Decimal("1295.00"),
                move_in_total=Decimal("2640.00"),
            )
        )

        # --- News items --------------------------------------------------
        now = datetime.now(timezone.utc)
        for i, item in enumerate(NEWS_ITEMS):
            db.add(
                models.NewsItem(
                    url_hash=hashlib.sha256(item["url"].encode()).hexdigest(),
                    title=item["title"],
                    source=item["source"],
                    url=item["url"],
                    category=item["category"],
                    zip=item["zip"],
                    published_at=now - timedelta(days=i + 1),
                    pinned=False,
                    hidden=False,
                )
            )

        # --- Pricing rules ----------------------------------------------
        for key, value in PRICING_RULES.items():
            db.add(models.PricingRule(key=key, value_json=value, updated_by="seed"))

        db.commit()
        print(
            f"Seeded: {len(plans)} floor plans, {len(units)} units, "
            f"{len(plans) * 24} price-history rows, {len(occupied)} leases, "
            f"{len(leads)} leads, 2 estimates, {len(NEWS_ITEMS)} news items, "
            f"{len(PRICING_RULES)} pricing rules."
        )


if __name__ == "__main__":
    seed()
