"""Estimate engine — all math driven by the pricing_rules table so the
office can tune values without a deploy."""
from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


class PricingError(ValueError):
    """Invalid input for the current pricing rules (unknown term, too many pets…)."""


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def load_rules(db: Session) -> dict:
    rows = db.scalars(select(models.PricingRule)).all()
    return {row.key: row.value_json for row in rows}


def compute_estimate(
    db: Session,
    *,
    floor_plan: models.FloorPlan,
    move_in_date: date,
    lease_term_months: int,
    pet_count: int,
    carports: int,
    furnished: bool,
) -> dict:
    rules = load_rules(db)

    term_premiums: dict = rules["term_premiums"]
    if str(lease_term_months) not in term_premiums:
        raise PricingError(
            f"Lease term must be one of {sorted(int(k) for k in term_premiums)} months."
        )

    pet_policy: dict = rules["pet_policy"]
    if pet_count > int(pet_policy["max_pets"]):
        raise PricingError(f"Maximum {pet_policy['max_pets']} pets per home.")

    base = money(floor_plan.base_rent)
    term_adjustment = money(base * Decimal(str(term_premiums[str(lease_term_months)])))

    seasonal_mult = Decimal(str(rules["seasonality_multipliers"][str(move_in_date.month)]))
    seasonality = money(base * (seasonal_mult - 1))

    pet_rent = money(pet_count * pet_policy["pet_rent_monthly"])

    carport_cfg: dict = rules["carports"]
    extra_carports = max(0, carports - int(carport_cfg["included"]))
    carport_rent = money(extra_carports * carport_cfg["extra_monthly"])

    furnished_premium = money(rules["furnished_premium_monthly"]) if furnished else money(0)

    monthly = base + term_adjustment + seasonality + pet_rent + carport_rent + furnished_premium

    fees: dict = rules["fees"]
    deposit = money(base * Decimal(str(fees["security_deposit_months"])))
    application_fee = money(fees["application_fee"])
    pet_fee = money(pet_policy["pet_fee_one_time"]) if pet_count else money(0)
    move_in_total = monthly + deposit + application_fee + pet_fee

    monthly_breakdown = [{"label": f"Base rent — {floor_plan.name}", "amount": float(base)}]
    if term_adjustment:
        monthly_breakdown.append(
            {"label": f"{lease_term_months}-month lease term", "amount": float(term_adjustment)}
        )
    if seasonality:
        monthly_breakdown.append(
            {
                "label": f"Seasonal adjustment ({move_in_date.strftime('%B')} move-in)",
                "amount": float(seasonality),
            }
        )
    if pet_rent:
        monthly_breakdown.append(
            {"label": f"Pet rent ({pet_count} × ${pet_policy['pet_rent_monthly']}/mo)",
             "amount": float(pet_rent)}
        )
    if carport_rent:
        monthly_breakdown.append(
            {"label": f"Additional carports ({extra_carports})", "amount": float(carport_rent)}
        )
    elif carports:
        monthly_breakdown.append({"label": "Assigned carport (included FREE)", "amount": 0.0})
    if furnished_premium:
        monthly_breakdown.append(
            {"label": "Furnished / corporate premium", "amount": float(furnished_premium)}
        )

    move_in_breakdown = [
        {"label": "First month's rent", "amount": float(monthly)},
        {"label": "Security deposit", "amount": float(deposit)},
        {"label": "Application fee", "amount": float(application_fee)},
    ]
    if pet_fee:
        move_in_breakdown.append({"label": "One-time pet fee", "amount": float(pet_fee)})

    return {
        "monthly_estimate": monthly,
        "move_in_total": move_in_total,
        "monthly_breakdown": monthly_breakdown,
        "move_in_breakdown": move_in_breakdown,
    }
