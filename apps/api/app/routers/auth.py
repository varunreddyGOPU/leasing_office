from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.ratelimit import rate_limit
from app.security import (
    COOKIE_NAME,
    SESSION_TTL_SECONDS,
    make_session_token,
    parse_session_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_current_resident(request: Request, db: Session = Depends(get_db)) -> models.Resident:
    token = request.cookies.get(COOKIE_NAME)
    resident_id = parse_session_token(token) if token else None
    resident = db.get(models.Resident, resident_id) if resident_id else None
    if resident is None:
        raise HTTPException(status_code=401, detail="Please sign in.")
    return resident


@router.post(
    "/login",
    response_model=schemas.ResidentOut,
    dependencies=[Depends(rate_limit("auth", per_minute=10))],
)
def login(
    payload: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)
) -> schemas.ResidentOut:
    resident = db.scalar(
        select(models.Resident).where(
            func.lower(models.Resident.email) == payload.email.strip().lower()
        )
    )
    if resident is None or not verify_password(payload.password, resident.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    response.set_cookie(
        COOKIE_NAME,
        make_session_token(resident.id),
        httponly=True,
        samesite="lax",
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )
    return schemas.ResidentOut.model_validate(resident)


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "signed_out"}


@router.get("/me", response_model=schemas.ResidentOut)
def me(resident: models.Resident = Depends(get_current_resident)) -> schemas.ResidentOut:
    return schemas.ResidentOut.model_validate(resident)
