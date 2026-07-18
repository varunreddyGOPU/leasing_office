from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db import engine
from app.routers import chat, estimates, floor_plans, leads, news

app = FastAPI(title="Auburn Ridge Leasing API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(floor_plans.router)
app.include_router(estimates.router)
app.include_router(leads.router)
app.include_router(news.router)
app.include_router(chat.router)


@app.get("/healthz")
def healthz() -> dict:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": db_ok, "env": settings.environment}
