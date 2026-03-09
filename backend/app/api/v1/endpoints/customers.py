"""CRM Müşteri API — KVKK uyumlu şifreli kişisel veri yönetimi."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.core.database import get_db
from app.core.deps import get_current_user, require_broker_or_advisor
from app.core.security import encrypt_field, decrypt_field
from app.models.customer import Customer
from app.models.user import User, UserRole
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerOut

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=list[CustomerOut])
async def list_customers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker_or_advisor),
):
    filters = [Customer.tenant_id == current_user.tenant_id, Customer.is_active == True]
    # Danışman sadece kendi müşterilerini görür
    if current_user.role == UserRole.ADVISOR:
        filters.append(Customer.assigned_advisor_id == current_user.id)

    q = await db.execute(
        select(Customer).where(and_(*filters))
        .order_by(Customer.created_at.desc())
        .offset((page - 1) * size).limit(size)
    )
    customers = q.scalars().all()
    return [_decrypt_customer(c) for c in customers]


@router.post("/", response_model=CustomerOut, status_code=201)
async def create_customer(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker_or_advisor),
):
    customer = Customer(
        tenant_id=current_user.tenant_id,
        assigned_advisor_id=current_user.id,
        full_name_encrypted=encrypt_field(payload.full_name),
        phone_encrypted=encrypt_field(payload.phone),
        email_encrypted=encrypt_field(payload.email) if payload.email else None,
        budget_min=payload.budget_min,
        budget_max=payload.budget_max,
        preferred_rooms=payload.preferred_rooms,
        preferred_districts=payload.preferred_districts,
        notes_encrypted=encrypt_field(payload.notes) if payload.notes else None,
    )
    db.add(customer)
    await db.flush()
    await db.refresh(customer)
    return _decrypt_customer(customer)


@router.get("/{customer_id}", response_model=CustomerOut)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker_or_advisor),
):
    customer = await _get_customer_with_access(customer_id, current_user, db)
    return _decrypt_customer(customer)


@router.patch("/{customer_id}", response_model=CustomerOut)
async def update_customer(
    customer_id: str,
    payload: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker_or_advisor),
):
    customer = await _get_customer_with_access(customer_id, current_user, db)

    if payload.full_name is not None:
        customer.full_name_encrypted = encrypt_field(payload.full_name)
    if payload.phone is not None:
        customer.phone_encrypted = encrypt_field(payload.phone)
    if payload.email is not None:
        customer.email_encrypted = encrypt_field(payload.email)
    if payload.budget_min is not None:
        customer.budget_min = payload.budget_min
    if payload.budget_max is not None:
        customer.budget_max = payload.budget_max
    if payload.preferred_rooms is not None:
        customer.preferred_rooms = payload.preferred_rooms
    if payload.preferred_districts is not None:
        customer.preferred_districts = payload.preferred_districts
    if payload.notes is not None:
        customer.notes_encrypted = encrypt_field(payload.notes)

    await db.flush()
    await db.refresh(customer)
    return _decrypt_customer(customer)


@router.delete("/{customer_id}", status_code=204)
async def deactivate_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker_or_advisor),
):
    customer = await _get_customer_with_access(customer_id, current_user, db)
    customer.is_active = False
    await db.flush()


async def _get_customer_with_access(customer_id: str, user: User, db: AsyncSession) -> Customer:
    filters = [Customer.id == customer_id, Customer.tenant_id == user.tenant_id]
    if user.role == UserRole.ADVISOR:
        filters.append(Customer.assigned_advisor_id == user.id)
    q = await db.execute(select(Customer).where(and_(*filters)))
    customer = q.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    return customer


def _decrypt_customer(c: Customer) -> CustomerOut:
    return CustomerOut(
        id=c.id,
        full_name=decrypt_field(c.full_name_encrypted),
        phone=decrypt_field(c.phone_encrypted),
        email=decrypt_field(c.email_encrypted) if c.email_encrypted else None,
        budget_min=c.budget_min,
        budget_max=c.budget_max,
        preferred_rooms=c.preferred_rooms,
        preferred_districts=c.preferred_districts,
        is_active=c.is_active,
        created_at=c.created_at,
        last_contact_at=c.last_contact_at,
        matched_listing_ids=c.matched_listing_ids,
    )
