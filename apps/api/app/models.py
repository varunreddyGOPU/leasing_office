"""SQLAlchemy 2.0 models — schema per 01-SYSTEM-DESIGN.md §8."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class FloorPlan(Base):
    __tablename__ = "floor_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    bedrooms: Mapped[int] = mapped_column(Integer)
    bathrooms: Mapped[Decimal] = mapped_column(Numeric(2, 1))
    sqft: Mapped[int] = mapped_column(Integer)
    base_rent: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    description: Mapped[str | None] = mapped_column(Text)

    units: Mapped[list[Unit]] = relationship(back_populates="floor_plan")


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True)
    floor_plan_id: Mapped[int] = mapped_column(ForeignKey("floor_plans.id"))
    unit_number: Mapped[str] = mapped_column(String(20), unique=True)
    tier: Mapped[str] = mapped_column(String(20), default="standard")  # standard | premium
    status: Mapped[str] = mapped_column(String(20), default="occupied")  # available | occupied | maintenance
    available_date: Mapped[date | None] = mapped_column(Date)

    floor_plan: Mapped[FloorPlan] = relationship(back_populates="units")
    leases: Mapped[list[Lease]] = relationship(back_populates="unit")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    floor_plan_id: Mapped[int] = mapped_column(ForeignKey("floor_plans.id"))
    effective_date: Mapped[date] = mapped_column(Date)
    asking_rent: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    source: Mapped[str] = mapped_column(String(20), default="internal")  # internal | comp


class Resident(Base):
    __tablename__ = "residents"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    leases: Mapped[list[Lease]] = relationship(back_populates="resident")


class Lease(Base):
    __tablename__ = "leases"

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    monthly_rent: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    auto_renew_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    renewal_offer_rent: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    renewal_status: Mapped[str] = mapped_column(String(20), default="none")  # none | offered | accepted | declined

    unit: Mapped[Unit] = relationship(back_populates="leases")
    resident: Mapped[Resident] = relationship(back_populates="leases")


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (UniqueConstraint("email", "phone", name="uq_leads_email_phone"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    desired_bedrooms: Mapped[int | None] = mapped_column(Integer)
    move_in_date: Mapped[date | None] = mapped_column(Date)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    pets: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), default="form")  # chatbot | form | phone
    status: Mapped[str] = mapped_column(String(20), default="new")  # new | contacted | toured | leased | lost
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    estimates: Mapped[list[Estimate]] = relationship(back_populates="lead")


class Estimate(Base):
    __tablename__ = "estimates"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"))
    floor_plan_id: Mapped[int] = mapped_column(ForeignKey("floor_plans.id"))
    inputs_json: Mapped[dict] = mapped_column(JSON)
    breakdown_json: Mapped[dict | None] = mapped_column(JSON)
    monthly_estimate: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    move_in_total: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped[Lead | None] = relationship(back_populates="estimates")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"))
    transcript_json: Mapped[list] = mapped_column(JSON, default=list)
    extracted_json: Mapped[dict | None] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MaintenanceTicket(Base):
    __tablename__ = "maintenance_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"))
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    photos: Mapped[list | None] = mapped_column(JSON)  # list of stored file paths/URLs
    status: Mapped[str] = mapped_column(String(20), default="new")  # new | scheduled | in_progress | resolved
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PricingRule(Base):
    __tablename__ = "pricing_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(60), unique=True)
    value_json: Mapped[dict | list | float | str] = mapped_column(JSON)
    updated_by: Mapped[str | None] = mapped_column(String(120))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PricingRecommendation(Base):
    __tablename__ = "pricing_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    floor_plan_id: Mapped[int] = mapped_column(ForeignKey("floor_plans.id"))
    month: Mapped[date] = mapped_column(Date)  # first of month
    recommended_rent: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    confidence_low: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    confidence_high: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    rationale: Mapped[str] = mapped_column(Text)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(500))
    source: Mapped[str | None] = mapped_column(String(120))
    url: Mapped[str] = mapped_column(String(1000))
    category: Mapped[str] = mapped_column(String(30), default="community")
    zip: Mapped[str] = mapped_column(String(10))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(40))  # renewal_window | rent_change | maintenance | availability | promo
    recipient_type: Mapped[str] = mapped_column(String(20))  # resident | lead
    recipient_id: Mapped[int] = mapped_column(Integer)
    payload_json: Mapped[dict] = mapped_column(JSON)
    send_after: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | sent | failed
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
