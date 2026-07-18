"""Estimate engine + lead/news endpoint tests (SQLite, no Redis — limiter fails open)."""
from datetime import date

from tests.test_smoke import client


def _july_next_year() -> str:
    return date(date.today().year + 1, 7, 1).isoformat()


def _estimate_payload(**overrides) -> dict:
    payload = {
        "floor_plan_id": 2,  # The Cedar, base $1,550
        "move_in_date": _july_next_year(),
        "lease_term_months": 12,
        "pets": [{"type": "cat", "count": 1}],
        "carports": 1,
        "furnished": False,
        "email": "estimate.tester@example.com",
        "name": "Estimate Tester",
        "phone": "248-555-0300",
    }
    payload.update(overrides)
    return payload


def test_estimate_math_cedar_july():
    r = client.post("/api/estimate", json=_estimate_payload())
    assert r.status_code == 200, r.text
    body = r.json()
    # base 1550 + 12-mo term 0 + July seasonality (+3% = 46.50) + pet 35 = 1631.50
    assert body["monthly_estimate"] == 1631.50
    # monthly + deposit 1550 + app fee 50 + pet fee 250
    assert body["move_in_total"] == 3481.50
    labels = [line["label"] for line in body["monthly_breakdown"]]
    assert any("Base rent" in l for l in labels)
    assert any("Seasonal" in l for l in labels)
    assert any("carport (included FREE)" in l for l in labels)
    assert "estimate" in body["disclaimer"].lower()


def test_estimate_furnished_short_term():
    r = client.post(
        "/api/estimate",
        json=_estimate_payload(pets=[], furnished=True, lease_term_months=6),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # base 1550 + 6-mo premium 8% (124.00) + July 46.50 + furnished 300 = 2020.50
    assert body["monthly_estimate"] == 2020.50
    # no pet fee: monthly + 1550 + 50
    assert body["move_in_total"] == 3620.50


def test_estimate_invalid_term_rejected():
    r = client.post("/api/estimate", json=_estimate_payload(lease_term_months=7))
    assert r.status_code == 422


def test_estimate_past_move_in_rejected():
    r = client.post("/api/estimate", json=_estimate_payload(move_in_date="2020-01-01"))
    assert r.status_code == 422


def test_estimate_dedupes_lead():
    # distinct phone so we exercise email-based dedupe, not phone matching
    r1 = client.post(
        "/api/estimate", json=_estimate_payload(email="dedupe@example.com", phone=None)
    )
    r2 = client.post(
        "/api/estimate",
        json=_estimate_payload(email="dedupe@example.com", phone=None, lease_term_months=9),
    )
    assert r1.status_code == 200 and r2.status_code == 200

    from sqlalchemy import func, select

    from app import models
    from app.db import SessionLocal

    with SessionLocal() as db:
        leads = db.scalar(
            select(func.count(models.Lead.id)).where(models.Lead.email == "dedupe@example.com")
        )
        estimates = db.scalar(
            select(func.count(models.Estimate.id))
            .join(models.Lead, models.Estimate.lead_id == models.Lead.id)
            .where(models.Lead.email == "dedupe@example.com")
        )
    assert leads == 1  # deduped
    assert estimates == 2  # but every estimate persisted


def test_contact_lead_dedupe_and_validation():
    payload = {
        "name": "Tour Seeker",
        "email": "tour.seeker@example.com",
        "phone": "248-555-0400",
        "desired_bedrooms": 2,
        "preferred_tour_at": "2027-03-02T14:00:00",
    }
    r1 = client.post("/api/leads", json=payload)
    r2 = client.post("/api/leads", json=payload)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]

    # neither email nor phone -> rejected
    r = client.post("/api/leads", json={"name": "Ghost"})
    assert r.status_code == 422


def test_news_endpoint():
    r = client.get("/api/news")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 3
    assert all(not i.get("hidden", False) for i in items)

    r = client.get("/api/news", params={"zip": "48326"})
    assert r.status_code == 200
    assert all(i["zip"] == "48326" for i in r.json())
