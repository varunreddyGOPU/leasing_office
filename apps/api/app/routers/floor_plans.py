from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db

router = APIRouter(prefix="/api", tags=["floor-plans"])


@router.get("/floor-plans", response_model=list[schemas.FloorPlanOut])
def list_floor_plans(db: Session = Depends(get_db)) -> list[schemas.FloorPlanOut]:
    plans = db.scalars(select(models.FloorPlan).order_by(models.FloorPlan.bedrooms)).all()
    out = []
    for plan in plans:
        current_rent = db.scalar(
            select(models.PriceHistory.asking_rent)
            .where(
                models.PriceHistory.floor_plan_id == plan.id,
                models.PriceHistory.source == "internal",
            )
            .order_by(models.PriceHistory.effective_date.desc())
            .limit(1)
        )
        available = db.scalar(
            select(func.count(models.Unit.id)).where(
                models.Unit.floor_plan_id == plan.id,
                models.Unit.status == "available",
            )
        )
        out.append(
            schemas.FloorPlanOut(
                id=plan.id,
                name=plan.name,
                bedrooms=plan.bedrooms,
                bathrooms=float(plan.bathrooms),
                sqft=plan.sqft,
                base_rent=float(plan.base_rent),
                description=plan.description,
                current_asking_rent=float(current_rent) if current_rent is not None else None,
                available_units=available or 0,
            )
        )
    return out


@router.get("/availability", response_model=list[schemas.UnitAvailabilityOut])
def list_availability(db: Session = Depends(get_db)) -> list[schemas.UnitAvailabilityOut]:
    rows = db.execute(
        select(models.Unit, models.FloorPlan)
        .join(models.FloorPlan, models.Unit.floor_plan_id == models.FloorPlan.id)
        .where(models.Unit.status == "available")
        .order_by(models.Unit.available_date)
    ).all()
    return [
        schemas.UnitAvailabilityOut(
            id=unit.id,
            unit_number=unit.unit_number,
            tier=unit.tier,
            status=unit.status,
            available_date=unit.available_date,
            floor_plan_id=plan.id,
            floor_plan_name=plan.name,
            bedrooms=plan.bedrooms,
            bathrooms=float(plan.bathrooms),
            sqft=plan.sqft,
        )
        for unit, plan in rows
    ]
