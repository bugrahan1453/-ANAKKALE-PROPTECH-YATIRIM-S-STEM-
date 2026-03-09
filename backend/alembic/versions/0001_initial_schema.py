"""İlk veritabanı şeması

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # tenants
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("plan", sa.String(50), server_default="starter"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("phone_encrypted", sa.String(500)),
        sa.Column("role", sa.String(20), nullable=False, server_default="advisor"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("last_login", sa.DateTime(timezone=True)),
    )

    # properties
    op.create_table(
        "properties",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("address_hash", sa.String(64), nullable=False, index=True),
        sa.Column("address_raw", sa.String(500)),
        sa.Column("district", sa.String(100)),
        sa.Column("neighborhood", sa.String(100)),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("sit_degree", sa.String(50)),
        sa.Column("zoning_status", sa.String(100)),
        sa.Column("is_olive_grove", sa.Boolean(), server_default="false"),
        sa.Column("legal_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # listings
    op.create_table(
        "listings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("property_id", sa.String(36), sa.ForeignKey("properties.id")),
        sa.Column("source_site", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(200), nullable=False),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("title", sa.String(500)),
        sa.Column("description", sa.Text()),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(10), server_default="TRY"),
        sa.Column("listing_type", sa.String(20), nullable=False, server_default="sale"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("city", sa.String(100)),
        sa.Column("district", sa.String(100), index=True),
        sa.Column("neighborhood", sa.String(200)),
        sa.Column("address_raw", sa.String(500)),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("area_m2", sa.Float()),
        sa.Column("room_count", sa.String(20), index=True),
        sa.Column("floor", sa.Integer()),
        sa.Column("total_floors", sa.Integer()),
        sa.Column("building_age", sa.Integer()),
        sa.Column("has_sea_view", sa.Boolean(), server_default="false"),
        sa.Column("features", postgresql.JSONB()),
        sa.Column("photo_hash", sa.String(100)),
        sa.Column("address_hash", sa.String(100)),
        sa.Column("is_fsbo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("motivation_score", sa.Integer()),
        sa.Column("visual_premium_score", sa.Float()),
        sa.Column("photo_quality_score", sa.Float()),
        sa.Column("price_signal", sa.String(10)),
        sa.Column("arv_estimate", sa.Float()),
        sa.Column("roi_years", sa.Float()),
        sa.Column("days_on_market", sa.Integer(), server_default="0"),
        sa.Column("real_days_on_market", sa.Integer(), server_default="0"),
        sa.Column("last_price_before_delete", sa.Float()),
        sa.Column("is_hidden_gem", sa.Boolean(), server_default="false"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("tenant_id", "source_site", "source_id", name="uq_listing_source"),
    )
    op.create_index("ix_listings_price", "listings", ["price"])
    op.create_index("ix_listings_motivation", "listings", ["motivation_score"])

    # listing_price_history (TimescaleDB hypertable)
    op.create_table(
        "listing_price_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("change_pct", sa.Float()),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), index=True),
    )

    # listing_photos
    op.create_table(
        "listing_photos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("local_path", sa.String(500)),
        sa.Column("perceptual_hash", sa.String(100)),
        sa.Column("order_index", sa.Integer(), server_default="0"),
        sa.Column("ai_features", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # customers
    op.create_table(
        "customers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("assigned_advisor_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("full_name_encrypted", sa.String(500), nullable=False),
        sa.Column("phone_encrypted", sa.String(500), nullable=False),
        sa.Column("email_encrypted", sa.String(500)),
        sa.Column("budget_min", sa.Float()),
        sa.Column("budget_max", sa.Float()),
        sa.Column("preferred_rooms", sa.String(100)),
        sa.Column("preferred_districts", sa.String(500)),
        sa.Column("notes_encrypted", sa.Text()),
        sa.Column("matched_listing_ids", postgresql.JSONB()),
        sa.Column("last_matched_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("last_contact_at", sa.DateTime(timezone=True)),
    )

    # tasks
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("assigned_to_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id")),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id")),
        sa.Column("task_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("priority", sa.Integer(), server_default="5"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("due_date", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # portfolios
    op.create_table(
        "portfolios",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id"), nullable=False),
        sa.Column("advisor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("is_exclusive", sa.Boolean(), server_default="false"),
        sa.Column("notes", sa.Text()),
    )

    # kvkk_consents
    op.create_table(
        "kvkk_consents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("consent_type", sa.String(50), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # data_requests
    op.create_table(
        "data_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("request_type", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("export_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    # RLS etkinleştir
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE listings ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE customers ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tasks ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE properties ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE kvkk_consents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE data_requests ENABLE ROW LEVEL SECURITY")

    # RLS policy — her tablo için tenant izolasyonu
    for table in ["users", "listings", "customers", "tasks", "portfolios", "properties", "kvkk_consents", "data_requests"]:
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = current_setting('app.current_tenant_id', true))
        """)


def downgrade() -> None:
    for table in ["data_requests", "kvkk_consents", "portfolios", "tasks", "customers",
                  "listing_photos", "listing_price_history", "listings", "properties",
                  "users", "tenants"]:
        op.drop_table(table)
