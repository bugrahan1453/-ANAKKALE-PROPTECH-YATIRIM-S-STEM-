import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    phone: str | None = None
    tenant_name: str | None = None   # sadece broker kayıtta gerekli


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == form_data.username, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı",
        )

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    token = create_access_token({"sub": user.id, "tenant_id": user.tenant_id, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Yeni broker kaydı. Her kayıt kendi tenant'ını oluşturur.
    Danışman eklemek için /users/ endpoint kullanılır.
    """
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")

    tenant_id = str(uuid.uuid4())
    tenant_name = body.tenant_name or f"{body.full_name} Emlak"

    tenant = Tenant(
        id=tenant_id,
        name=tenant_name,
        slug=tenant_name.lower().replace(" ", "-")[:50],
    )
    db.add(tenant)

    user = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        email=body.email,
        full_name=body.full_name,
        hashed_password=get_password_hash(body.password),
        role=UserRole.BROKER,
    )
    db.add(user)
    await db.commit()

    token = create_access_token({"sub": user.id, "tenant_id": tenant_id, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role, "tenant_id": tenant_id}


@router.post("/change-password")
async def change_password(
    body: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mevcut şifreyi doğrulayarak yeni şifreye geç."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mevcut şifre hatalı")

    current_user.hashed_password = get_password_hash(body.new_password)
    await db.commit()
    return {"message": "Şifre başarıyla değiştirildi"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Giriş yapmış kullanıcının profili."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
        "last_login": current_user.last_login,
    }
