"""
Kullanıcı modeli — RBAC rolleri: broker | advisor | assistant
"""
import enum
import uuid
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserRole(str, enum.Enum):
    BROKER = "broker"       # Tüm veriler + Yatırım Radarı
    ADVISOR = "advisor"     # Sadece atanan portföyler ve kendi müşterileri
    ASSISTANT = "assistant" # Sadece evrak ve görev takibi


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    hashed_password: Mapped[str] = mapped_column(String(255))
    phone_encrypted: Mapped[str | None] = mapped_column(String(500))  # Fernet şifreli
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.ADVISOR)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="assigned_to")
    portfolios: Mapped[list["Portfolio"]] = relationship("Portfolio", back_populates="advisor")
