"""
Multi-Tenant modeli — Her emlak ofisi bir Tenant'tır.
Row-Level Security (RLS) tüm tablolarda tenant_id üzerinden çalışır.
"""
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    plan: Mapped[str] = mapped_column(String(50), default="starter")  # starter | pro | enterprise
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")
    listings: Mapped[list["Listing"]] = relationship("Listing", back_populates="tenant")
    customers: Mapped[list["Customer"]] = relationship("Customer", back_populates="tenant")
