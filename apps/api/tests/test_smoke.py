"""Smoke tests. DATABASE_URL is pinned to throwaway SQLite in conftest.py,
which pytest imports before any test module."""
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app
from app.seed import seed

# Hard guard: tests must never run against a real database.
assert engine.url.get_backend_name() == "sqlite", (
    f"Tests must use SQLite, got {engine.url.get_backend_name()} — "
    "conftest.py did not run first?"
)

Base.metadata.create_all(engine)
seed()
client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_floor_plans_seeded():
    r = client.get("/api/floor-plans")
    assert r.status_code == 200
    plans = r.json()
    assert len(plans) == 3
    assert [p["bedrooms"] for p in plans] == [1, 2, 3]
    for p in plans:
        assert p["current_asking_rent"] is not None


def test_availability():
    r = client.get("/api/availability")
    assert r.status_code == 200
    units = r.json()
    # Seed leaves one vacant unit per floor plan; other tests (renewal
    # decline) may legitimately add more.
    assert len(units) >= 3
    assert all(u["status"] == "available" for u in units)
    assert {u["bedrooms"] for u in units} == {1, 2, 3}
