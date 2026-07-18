from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.ratelimit import rate_limit
from app.services.leads import upsert_lead
from app.services.pricing import PricingError, compute_estimate

router = APIRouter(prefix="/api", tags=["estimates"])

DISCLAIMER = (
    "This is an estimate based on current sample pricing. The leasing office "
    "confirms final pricing and availability — call 248-377-2680."
)


@router.post(
    "/estimate",
    response_model=schemas.EstimateResponse,
    dependencies=[Depends(rate_limit("estimate", per_minute=20))],
)
def create_estimate(
    payload: schemas.EstimateRequest, db: Session = Depends(get_db)
) -> schemas.EstimateResponse:
    plan = db.get(models.FloorPlan, payload.floor_plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Unknown floor plan.")

    pet_count = sum(p.count for p in payload.pets)
    try:
        result = compute_estimate(
            db,
            floor_plan=plan,
            move_in_date=payload.move_in_date,
            lease_term_months=payload.lease_term_months,
            pet_count=pet_count,
            carports=payload.carports,
            furnished=payload.furnished,
        )
    except PricingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    lead = upsert_lead(
        db,
        email=payload.email,
        phone=payload.phone,
        source="form",
        name=payload.name,
        desired_bedrooms=plan.bedrooms,
        move_in_date=payload.move_in_date,
        pets=", ".join(f"{p.count} {p.type}" for p in payload.pets) or None,
    )

    estimate = models.Estimate(
        lead_id=lead.id,
        floor_plan_id=plan.id,
        inputs_json=payload.model_dump(mode="json"),
        breakdown_json={
            "monthly": result["monthly_breakdown"],
            "move_in": result["move_in_breakdown"],
        },
        monthly_estimate=result["monthly_estimate"],
        move_in_total=result["move_in_total"],
    )
    db.add(estimate)
    db.commit()

    return schemas.EstimateResponse(
        estimate_id=estimate.id,
        floor_plan_name=plan.name,
        monthly_estimate=float(result["monthly_estimate"]),
        move_in_total=float(result["move_in_total"]),
        monthly_breakdown=result["monthly_breakdown"],
        move_in_breakdown=result["move_in_breakdown"],
        disclaimer=DISCLAIMER,
    )
