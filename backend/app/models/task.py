"""Görev modeli — CRM sıfır inisiyatif görev yöneticisi."""
import enum
import uuid
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SAEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TaskType(str, enum.Enum):
    COLD_CALL = "cold_call"
    FOLLOW_UP = "follow_up"
    SHOWING = "showing"
    NEIGHBOR_RADAR = "neighbor_radar"
    PRICE_DROP_ALERT = "price_drop_alert"
    BUYER_MATCH = "buyer_match"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    SKIPPED = "skipped"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    assigned_to_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    listing_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("listings.id"))
    customer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("customers.id"))

    task_type: Mapped[TaskType] = mapped_column(SAEnum(TaskType))
    status: Mapped[TaskStatus] = mapped_column(SAEnum(TaskStatus), default=TaskStatus.PENDING)
    title: Mapped[str] = mapped_column(String(500))
    script: Mapped[str | None] = mapped_column(Text)  # Tele-prompter senaryosu
    priority: Mapped[int] = mapped_column(default=5)  # 1 (en yüksek) - 10

    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    due_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assigned_to: Mapped["User"] = relationship("User", back_populates="tasks")
