"""Prompt assembly and defensive lead extraction for Ridgeline Assistant."""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models

PROMPT_TEMPLATE = Path(__file__).resolve().parent.parent / "prompts" / "chatbot_system.md"

OFFICE_HOURS = (
    "OFFICE: Mon-Fri 9:30am-5:00pm | phone 248-377-2680 | email Auburnridge@633pros.com"
)

STATIC_FACTS = """PROPERTY FACTS:
- Auburn Ridge Townhomes, 2610 Davison Ave, Auburn Hills, MI 48326 (theauburnridge.com).
- 1, 2 & 3 bedroom townhomes/condos. Every home: private entry, in-home washer & dryer,
  patio or balcony, electric fireplace; floor plans include master suites.
- Amenities: seasonal pool with sundeck, 24-hour renovated fitness center, FREE assigned
  carports, tree-lined quiet community, pet friendly, corporate/furnished rentals available.
- Pet policy (sample pricing): cats & dogs welcome, max 2; $35/mo pet rent per pet plus
  $250 one-time fee. Furnished/corporate premium: +$300/mo (sample).
- Lease terms: 6, 9, 12, or 15 months. The website's Instant Estimate tool gives an
  itemized estimate.
- Location: 5 min from Oakland University; under 10 min to Village of Rochester Hills,
  Trader Joe's, Whole Foods; easy commute to Chrysler, UWM, GM, Troy; near Top Golf,
  Paint Creek Trail, Meadowbrook Theater, Great Lakes Crossing, Pine Knob."""

FALLBACK_MESSAGE = (
    "I'm having trouble connecting right now — sorry about that! Please call the "
    "leasing office at 248-377-2680 (Mon-Fri 9:30am-5pm) or email "
    "Auburnridge@633pros.com and they'll be happy to help."
)

EXTRACTION_INSTRUCTION = (
    "Extract from this conversation as strict JSON: "
    '{"name", "phone", "email", "desired_bedrooms", "move_in_date", "budget", '
    '"pets", "notes"}. Use null for unknown. move_in_date must be YYYY-MM-DD. '
    "Respond with JSON only."
)


def build_system_prompt(db: Session) -> str:
    plans = db.scalars(select(models.FloorPlan).order_by(models.FloorPlan.bedrooms)).all()
    plan_lines = []
    for plan in plans:
        rent = db.scalar(
            select(models.PriceHistory.asking_rent)
            .where(
                models.PriceHistory.floor_plan_id == plan.id,
                models.PriceHistory.source == "internal",
            )
            .order_by(models.PriceHistory.effective_date.desc())
            .limit(1)
        )
        plan_lines.append(
            f"- {plan.name}: {plan.bedrooms} bed / {plan.bathrooms} bath, ~{plan.sqft} sqft, "
            f"from ${rent or plan.base_rent}/mo (sample estimate)"
        )

    available = db.execute(
        select(models.Unit, models.FloorPlan)
        .join(models.FloorPlan, models.Unit.floor_plan_id == models.FloorPlan.id)
        .where(models.Unit.status == "available")
        .order_by(models.Unit.available_date)
    ).all()
    if available:
        avail_lines = [
            f"- {plan.name} ({plan.bedrooms} bed) unit {unit.unit_number}: available "
            f"{unit.available_date:%B %d, %Y}" if unit.available_date
            else f"- {plan.name} ({plan.bedrooms} bed) unit {unit.unit_number}: available now"
            for unit, plan in available
        ]
    else:
        avail_lines = ["- No units currently listed; offer the waitlist via the office."]

    facts = STATIC_FACTS + "\nFLOOR PLANS:\n" + "\n".join(plan_lines)
    availability = "CURRENT AVAILABILITY:\n" + "\n".join(avail_lines)

    template = PROMPT_TEMPLATE.read_text()
    return (
        template.replace("{property_facts}", facts)
        .replace("{current_availability}", availability)
        .replace("{office_hours}", OFFICE_HOURS)
    )


def parse_extracted(raw: str) -> dict:
    """Parse the extraction model's reply defensively: strip code fences, find
    the outermost JSON object, coerce field types, drop anything malformed."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return {}
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}

    def clean_str(value, limit: int) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value[:limit] or None

    out: dict = {
        "name": clean_str(data.get("name"), 120),
        "phone": clean_str(data.get("phone"), 30),
        "email": clean_str(data.get("email"), 255),
        "pets": clean_str(data.get("pets"), 120),
        "notes": clean_str(data.get("notes"), 2000),
        "desired_bedrooms": None,
        "move_in_date": None,
        "budget": None,
    }
    if out["email"] and "@" not in out["email"]:
        out["email"] = None
    try:
        bedrooms = int(data.get("desired_bedrooms"))
        if 1 <= bedrooms <= 3:
            out["desired_bedrooms"] = bedrooms
    except (TypeError, ValueError):
        pass
    try:
        parsed = datetime.strptime(str(data.get("move_in_date")), "%Y-%m-%d").date()
        if parsed >= date(2000, 1, 1):
            out["move_in_date"] = parsed
    except (TypeError, ValueError):
        pass
    try:
        budget = float(str(data.get("budget")).replace("$", "").replace(",", ""))
        if 0 < budget < 100000:
            out["budget"] = round(budget, 2)
    except (TypeError, ValueError):
        pass
    return out
