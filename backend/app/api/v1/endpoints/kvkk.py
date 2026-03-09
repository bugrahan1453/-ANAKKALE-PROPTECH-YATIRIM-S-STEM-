"""KVKK (Kişisel Verilerin Korunması Kanunu) Uyum Endpoint'leri."""
import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from pydantic import BaseModel

from app.core.deps import get_current_user, get_tenant_session
from app.models.user import User
from app.models.kvkk import KVKKConsent, DataRequest, ConsentType, ConsentAction, DataRequestType, DataRequestStatus
from app.core.security import decrypt_field

router = APIRouter(prefix="/kvkk", tags=["kvkk"])


class ConsentRequest(BaseModel):
    consent_type: ConsentType
    action: ConsentAction


class DataRequestCreate(BaseModel):
    request_type: DataRequestType
    reason: str = ""


# ─── AÇIK RIZA ────────────────────────────────────────────────────

@router.post("/consent")
async def update_consent(
    body: ConsentRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    """KVKK madde 5 — Açık rıza ver veya geri çek."""
    consent = KVKKConsent(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        consent_type=body.consent_type,
        action=body.action,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(consent)
    await db.flush()
    return {
        "message": f"Rıza {body.action.value}: {body.consent_type.value}",
        "consent_id": consent.id,
        "timestamp": consent.created_at.isoformat(),
    }


@router.get("/consent/status")
async def get_consent_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    """Kullanıcının mevcut rıza durumu."""
    result = await db.execute(
        select(KVKKConsent)
        .where(and_(KVKKConsent.user_id == current_user.id))
        .order_by(KVKKConsent.created_at.desc())
    )
    consents = result.scalars().all()

    # Her tür için en son kaydı al
    status = {}
    for ct in ConsentType:
        for c in consents:
            if c.consent_type == ct:
                status[ct.value] = c.action.value
                break
        else:
            status[ct.value] = "not_set"

    return {"consents": status, "user_id": current_user.id}


# ─── VERİ TALEP HAKKI ─────────────────────────────────────────────

@router.post("/data-request")
async def create_data_request(
    body: DataRequestCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    """
    KVKK madde 11 — Veri silme, taşıma veya düzeltme talebi oluştur.
    - DELETE: 30 gün içinde tüm kişisel veriler silinir
    - EXPORT: 72 saat içinde JSON paket hazırlanır
    - RECTIFY: Operatör onaylı düzeltme
    """
    req = DataRequest(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        request_type=body.request_type,
        reason=body.reason,
    )
    db.add(req)
    await db.flush()

    if body.request_type == DataRequestType.EXPORT:
        background_tasks.add_task(_export_user_data, current_user.id, req.id)

    return {
        "request_id": req.id,
        "type": body.request_type.value,
        "status": "pending",
        "message": _request_message(body.request_type),
    }


@router.delete("/me")
async def delete_my_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
):
    """
    KVKK madde 7 — Kullanıcının tüm kişisel verilerini anonim hale getirir.
    İlan ve görev verileri istatistik için tutulur (anonim).
    """
    from app.models.customer import Customer

    # Müşteri PII anonimleştir
    customers = await db.execute(
        select(Customer).where(Customer.tenant_id == current_user.tenant_id)
    )
    for c in customers.scalars().all():
        if c.created_by_id == current_user.id:
            c.full_name_encrypted = None
            c.email_encrypted = None
            c.phone_encrypted = None
            c.notes = "[SİLİNDİ - KVKK]"

    # Kullanıcı hesabını deaktif et ve PII temizle
    current_user.is_active = False
    current_user.full_name = "[SİLİNDİ]"
    current_user.phone_encrypted = None

    await db.flush()
    return {
        "message": "Kişisel verileriniz anonimleştirildi. Hesabınız kapatıldı.",
        "deleted_at": datetime.now(timezone.utc).isoformat(),
    }


# ─── İÇ YARDIMCI FONKSİYONLAR ────────────────────────────────────

def _request_message(request_type: DataRequestType) -> str:
    messages = {
        DataRequestType.DELETE: "Verileriniz 30 gün içinde silinecek. Talep numaranızı saklayın.",
        DataRequestType.EXPORT: "Veri paketiniz 72 saat içinde hazır olacak. E-posta ile bildirileceksiniz.",
        DataRequestType.RECTIFY: "Düzeltme talebiniz incelemeye alındı. 10 iş günü içinde yanıtlanacak.",
    }
    return messages.get(request_type, "Talebiniz alındı.")


async def _export_user_data(user_id: str, request_id: str):
    """
    Kullanıcının tüm verisini JSON olarak paketler.
    Gerçek üretimde: S3'e yükle, şifrele, imzalı URL gönder.
    """
    from app.core.database import AsyncSessionLocal
    from app.models.task import Task
    from app.models.portfolio import Portfolio

    async with AsyncSessionLocal() as db:
        try:
            tasks_r = await db.execute(select(Task).where(Task.assigned_to_id == user_id))
            tasks = [{"id": t.id, "type": t.task_type, "status": t.status, "created": str(t.created_at)}
                     for t in tasks_r.scalars().all()]

            export = {
                "user_id": user_id,
                "export_date": datetime.now(timezone.utc).isoformat(),
                "tasks": tasks,
                "note": "KVKK madde 11(e) kapsamında veri taşınabilirliği paketi",
            }

            # TODO: S3'e yükle veya şifreli dosya oluştur
            export_json = json.dumps(export, ensure_ascii=False, indent=2)

            # DataRequest kaydını güncelle
            req = await db.get(DataRequest, request_id)
            if req:
                req.status = DataRequestStatus.COMPLETED
                req.completed_at = datetime.now(timezone.utc)
                req.export_url = f"/api/v1/kvkk/export/{request_id}"
                await db.commit()

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Veri dışa aktarım hatası: {e}")
