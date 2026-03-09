"""KVKK Uyum Modelleri — Açık Rıza, Silme Talepleri, Veri Taşınabilirliği."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class ConsentType(str, enum.Enum):
    MARKETING = "marketing"
    PROFILING = "profiling"
    THIRD_PARTY = "third_party"
    COMMUNICATION = "communication"


class ConsentAction(str, enum.Enum):
    GRANTED = "granted"
    WITHDRAWN = "withdrawn"


class DataRequestType(str, enum.Enum):
    DELETE = "delete"
    EXPORT = "export"
    RECTIFY = "rectify"


class DataRequestStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class KVKKConsent(Base):
    """Kullanıcı açık rıza kayıtları."""
    __tablename__ = "kvkk_consents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    consent_type = Column(SAEnum(ConsentType), nullable=False)
    action = Column(SAEnum(ConsentAction), nullable=False)
    ip_address = Column(String)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class DataRequest(Base):
    """Kişisel veri erişim/silme/düzeltme talepleri."""
    __tablename__ = "data_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    request_type = Column(SAEnum(DataRequestType), nullable=False)
    status = Column(SAEnum(DataRequestStatus), default=DataRequestStatus.PENDING)
    reason = Column(Text)
    completed_at = Column(DateTime(timezone=True))
    export_url = Column(String)  # Veri dışa aktarım dosyası URL
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
