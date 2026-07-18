from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class FloorPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    bedrooms: int
    bathrooms: float
    sqft: int
    base_rent: float
    description: str | None = None
    current_asking_rent: float | None = None
    available_units: int = 0


class UnitAvailabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unit_number: str
    tier: str
    status: str
    available_date: date | None = None
    floor_plan_id: int
    floor_plan_name: str
    bedrooms: int
    bathrooms: float
    sqft: int


class PetInput(BaseModel):
    type: Literal["cat", "dog"]
    count: int = Field(1, ge=1, le=4)


class EstimateRequest(BaseModel):
    floor_plan_id: int
    move_in_date: date
    lease_term_months: Literal[6, 9, 12, 15]
    pets: list[PetInput] = []
    carports: int = Field(1, ge=0, le=3)
    furnished: bool = False
    # Lead capture — email required to view the full breakdown.
    email: EmailStr
    name: str | None = Field(None, max_length=120)
    phone: str | None = Field(None, max_length=30)

    @field_validator("move_in_date")
    @classmethod
    def not_in_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Move-in date cannot be in the past.")
        return v


class EstimateLineItem(BaseModel):
    label: str
    amount: float


class EstimateResponse(BaseModel):
    estimate_id: int
    floor_plan_name: str
    monthly_estimate: float
    move_in_total: float
    monthly_breakdown: list[EstimateLineItem]
    move_in_breakdown: list[EstimateLineItem]
    disclaimer: str


class LeadCreate(BaseModel):
    name: str = Field(..., max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=30)
    desired_bedrooms: int | None = Field(None, ge=1, le=3)
    preferred_tour_at: datetime | None = None
    notes: str | None = Field(None, max_length=2000)

    @model_validator(mode="after")
    def email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Provide an email or a phone number so we can reach you.")
        return self


class LeadOut(BaseModel):
    id: int
    status: str
    message: str


class NewsItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source: str | None = None
    url: str
    category: str
    zip: str
    published_at: datetime | None = None
    pinned: bool
