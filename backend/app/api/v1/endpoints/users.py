"""Kullanıcı ve Tenant yönetimi API."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user, require_broker
from app.core.security import get_password_hash, encrypt_field
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.schemas.user import UserCreate, UserOut, UserUpdate, TenantCreate, TenantOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    q = await db.execute(
        select(User).where(User.tenant_id == current_user.tenant_id).order_by(User.full_name)
    )
    return q.scalars().all()


@router.post("/", response_model=UserOut, status_code=201)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")

    user = User(
        tenant_id=current_user.tenant_id,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        phone_encrypted=encrypt_field(payload.phone) if payload.phone else None,
        role=UserRole(payload.role),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    q = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == current_user.tenant_id)
    )
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        user.email = payload.email
    if payload.role is not None:
        user.role = UserRole(payload.role)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.phone is not None:
        user.phone_encrypted = encrypt_field(payload.phone)

    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    q = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == current_user.tenant_id)
    )
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    user.is_active = False
    await db.flush()


# ─── Tenant ──────────────────────────────────────
@router.get("/tenant", response_model=TenantOut)
async def get_tenant(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    return q.scalar_one()
