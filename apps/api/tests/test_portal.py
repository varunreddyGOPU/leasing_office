"""Resident portal: auth, lease + renewal offer/accept/decline, maintenance."""
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from app import models
from app.db import SessionLocal
from app.main import app
from tests.test_smoke import client

ADMIN = {"X-Admin-Key": "test-admin"}


def login(n: int) -> None:
    r = client.post(
        "/api/auth/login",
        json={"email": f"resident{n}@example.com", "password": "auburn-demo"},
    )
    assert r.status_code == 200, r.text


def test_login_rejects_bad_password():
    r = client.post(
        "/api/auth/login",
        json={"email": "resident1@example.com", "password": "wrong"},
    )
    assert r.status_code == 401


def test_lease_requires_auth():
    fresh = TestClient(app)  # no cookies
    assert fresh.get("/api/me/lease").status_code == 401


def test_lease_view_and_offer_math():
    login(1)  # seeded: lease ends within ~1-2 months -> inside the T-95 window
    r = client.get("/api/me/lease")
    assert r.status_code == 200
    body = r.json()
    lease = body["lease"]
    assert lease is not None
    assert 0 <= lease["days_to_end"] <= 95
    assert lease["renewal_status"] == "offered"
    assert lease["unit"]["unit_number"].startswith("2610-")

    # offer = min(latest asking rent for the plan, current_rent * 1.05)
    with SessionLocal() as db:
        db_lease = db.get(models.Lease, lease["id"])
        asking = db.scalar(
            select(models.PriceHistory.asking_rent)
            .where(
                models.PriceHistory.floor_plan_id == db_lease.unit.floor_plan_id,
                models.PriceHistory.source == "internal",
            )
            .order_by(models.PriceHistory.effective_date.desc())
            .limit(1)
        )
        expected = min(
            Decimal(asking).quantize(Decimal("0.01")),
            (Decimal(db_lease.monthly_rent) * Decimal("1.05")).quantize(Decimal("0.01")),
        )
    assert Decimal(str(lease["renewal_offer_rent"])) == expected

    # An alert-outbox row was queued for the offer.
    with SessionLocal() as db:
        alert = db.scalar(
            select(models.Alert).where(
                models.Alert.type == "renewal_offer",
                models.Alert.recipient_id == body["resident"]["id"],
            )
        )
        assert alert is not None and alert.status == "pending"


def test_accept_renewal_creates_upcoming_lease():
    login(1)
    r = client.post("/api/me/renewal", json={"action": "accept"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["lease"]["renewal_status"] == "accepted"
    up = body["upcoming_lease"]
    assert up is not None
    assert up["monthly_rent"] == body["lease"]["renewal_offer_rent"]
    assert date.fromisoformat(up["start_date"]) > date.fromisoformat(body["lease"]["end_date"])

    # One-click is one-shot: no open offer remains.
    assert client.post("/api/me/renewal", json={"action": "accept"}).status_code == 409

    with SessionLocal() as db:
        assert (
            db.scalar(
                select(models.Alert).where(models.Alert.type == "renewal_confirmed")
            )
            is not None
        )


def test_decline_renewal_flags_unit_available():
    login(2)
    r = client.get("/api/me/lease")
    lease = r.json()["lease"]
    assert lease["renewal_status"] == "offered"

    r = client.post("/api/me/renewal", json={"action": "decline"})
    assert r.status_code == 200
    assert r.json()["lease"]["renewal_status"] == "declined"

    with SessionLocal() as db:
        db_lease = db.get(models.Lease, lease["id"])
        assert db_lease.unit.status == "available"
        assert db_lease.unit.available_date == db_lease.end_date.replace(
            day=db_lease.end_date.day
        ) + __import__("datetime").timedelta(days=1)
        assert (
            db.scalar(select(models.Alert).where(models.Alert.type == "renewal_declined"))
            is not None
        )


def test_maintenance_flow_with_photo():
    login(3)
    r = client.post(
        "/api/me/maintenance",
        data={"category": "plumbing", "description": "Kitchen faucet drips constantly."},
        files=[("photos", ("leak.png", b"\x89PNG-fake-bytes", "image/png"))],
    )
    assert r.status_code == 200, r.text
    ticket_id = r.json()["id"]

    r = client.get("/api/me/maintenance")
    mine = [t for t in r.json() if t["id"] == ticket_id]
    assert mine and mine[0]["status"] == "new" and mine[0]["photo_count"] == 1

    # Owner can fetch the photo…
    assert client.get(f"/api/me/maintenance/{ticket_id}/photos/0").status_code == 200
    # …someone else cannot.
    login(4)
    assert client.get(f"/api/me/maintenance/{ticket_id}/photos/0").status_code == 404

    # Bad category / oversized photo count rejected.
    login(3)
    r = client.post(
        "/api/me/maintenance",
        data={"category": "nonsense", "description": "hello world"},
    )
    assert r.status_code == 422


def test_admin_kanban_and_alerts():
    assert client.get("/api/admin/maintenance").status_code == 401

    r = client.get("/api/admin/maintenance", headers=ADMIN)
    assert r.status_code == 200
    tickets = r.json()
    assert tickets and "unit_number" in tickets[0]
    tid = tickets[0]["id"]

    r = client.post(
        f"/api/admin/maintenance/{tid}/status", headers=ADMIN, json={"status": "scheduled"}
    )
    assert r.status_code == 200 and r.json()["status"] == "scheduled"
    # Same status again -> conflict.
    assert (
        client.post(
            f"/api/admin/maintenance/{tid}/status", headers=ADMIN, json={"status": "scheduled"}
        ).status_code
        == 409
    )
    r = client.post(
        f"/api/admin/maintenance/{tid}/status", headers=ADMIN, json={"status": "resolved"}
    )
    assert r.json()["resolved_at"] is not None

    with SessionLocal() as db:
        statuses = db.scalars(
            select(models.Alert.payload_json).where(models.Alert.type == "maintenance_status")
        ).all()
        assert {p["status"] for p in statuses} >= {"scheduled", "resolved"}
