"""initial schema — all core tables

Revision ID: 0001
Revises:
Create Date: 2026-07-18

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "floor_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("bedrooms", sa.Integer(), nullable=False),
        sa.Column("bathrooms", sa.Numeric(2, 1), nullable=False),
        sa.Column("sqft", sa.Integer(), nullable=False),
        sa.Column("base_rent", sa.Numeric(8, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    op.create_table(
        "residents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("desired_bedrooms", sa.Integer(), nullable=True),
        sa.Column("move_in_date", sa.Date(), nullable=True),
        sa.Column("budget", sa.Numeric(8, 2), nullable=True),
        sa.Column("pets", sa.String(120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("email", "phone", name="uq_leads_email_phone"),
    )

    op.create_table(
        "units",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("floor_plan_id", sa.Integer(), sa.ForeignKey("floor_plans.id"), nullable=False),
        sa.Column("unit_number", sa.String(20), nullable=False, unique=True),
        sa.Column("tier", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("available_date", sa.Date(), nullable=True),
    )

    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("floor_plan_id", sa.Integer(), sa.ForeignKey("floor_plans.id"), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("asking_rent", sa.Numeric(8, 2), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
    )
    op.create_index("ix_price_history_plan_date", "price_history", ["floor_plan_id", "effective_date"])

    op.create_table(
        "leases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("unit_id", sa.Integer(), sa.ForeignKey("units.id"), nullable=False),
        sa.Column("resident_id", sa.Integer(), sa.ForeignKey("residents.id"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("monthly_rent", sa.Numeric(8, 2), nullable=False),
        sa.Column("auto_renew_opt_in", sa.Boolean(), nullable=False),
        sa.Column("renewal_offer_rent", sa.Numeric(8, 2), nullable=True),
        sa.Column("renewal_status", sa.String(20), nullable=False),
    )
    op.create_index("ix_leases_end_date", "leases", ["end_date"])

    op.create_table(
        "estimates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id"), nullable=True),
        sa.Column("floor_plan_id", sa.Integer(), sa.ForeignKey("floor_plans.id"), nullable=False),
        sa.Column("inputs_json", sa.JSON(), nullable=False),
        sa.Column("breakdown_json", sa.JSON(), nullable=True),
        sa.Column("monthly_estimate", sa.Numeric(8, 2), nullable=False),
        sa.Column("move_in_total", sa.Numeric(8, 2), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id"), nullable=True),
        sa.Column("transcript_json", sa.JSON(), nullable=False),
        sa.Column("extracted_json", sa.JSON(), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "maintenance_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("unit_id", sa.Integer(), sa.ForeignKey("units.id"), nullable=False),
        sa.Column("resident_id", sa.Integer(), sa.ForeignKey("residents.id"), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("photos", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "pricing_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(60), nullable=False, unique=True),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("updated_by", sa.String(120), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "pricing_recommendations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("floor_plan_id", sa.Integer(), sa.ForeignKey("floor_plans.id"), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("recommended_rent", sa.Numeric(8, 2), nullable=False),
        sa.Column("confidence_low", sa.Numeric(8, 2), nullable=False),
        sa.Column("confidence_high", sa.Numeric(8, 2), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "news_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("url_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source", sa.String(120), nullable=True),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("zip", sa.String(10), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pinned", sa.Boolean(), nullable=False),
        sa.Column("hidden", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("recipient_type", sa.String(20), nullable=False),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("send_after", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index("ix_alerts_status_send_after", "alerts", ["status", "send_after"])


def downgrade() -> None:
    for table in (
        "alerts",
        "news_items",
        "pricing_recommendations",
        "pricing_rules",
        "maintenance_tickets",
        "chat_sessions",
        "estimates",
        "leases",
        "price_history",
        "units",
        "leads",
        "residents",
        "floor_plans",
    ):
        op.drop_table(table)
