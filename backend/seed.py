#!/usr/bin/env python3
"""
İlk kurulum seed scripti.
Tenant, broker ve 3 danışman oluşturur.

Kullanım:
    cd backend
    python seed.py

    # Özel bilgilerle:
    python seed.py --office "Kale Emlak" --email admin@kale.com --password GucluSifre123
"""
import asyncio
import argparse
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.tenant import Tenant
from app.models.user import User, UserRole


async def seed(office_name: str, broker_email: str, broker_password: str):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Tenant zaten var mı?
        existing_tenant = await db.execute(select(Tenant).where(Tenant.slug == office_name.lower().replace(" ", "-")[:50]))
        if existing_tenant.scalar_one_or_none():
            print(f"✓ Tenant '{office_name}' zaten mevcut, atlanıyor...")
        else:
            tenant_id = str(uuid.uuid4())
            tenant = Tenant(
                id=tenant_id,
                name=office_name,
                slug=office_name.lower().replace(" ", "-")[:50],
                is_active=True,
                plan="pro",
            )
            db.add(tenant)
            await db.flush()
            print(f"✓ Tenant oluşturuldu: {office_name} ({tenant_id})")

            # Broker
            broker = User(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                email=broker_email,
                full_name="Ofis Müdürü",
                hashed_password=get_password_hash(broker_password),
                role=UserRole.BROKER,
            )
            db.add(broker)
            print(f"✓ Broker oluşturuldu: {broker_email}")

            # 3 Danışman
            advisors = [
                ("Danışman Ahmet Kaya", f"ahmet.kaya@{office_name.lower().replace(' ', '')}.com"),
                ("Danışman Fatma Demir", f"fatma.demir@{office_name.lower().replace(' ', '')}.com"),
                ("Danışman Mehmet Çelik", f"mehmet.celik@{office_name.lower().replace(' ', '')}.com"),
            ]
            default_advisor_pass = get_password_hash("Danisман123!")
            for name, email in advisors:
                advisor = User(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    email=email,
                    full_name=name,
                    hashed_password=default_advisor_pass,
                    role=UserRole.ADVISOR,
                )
                db.add(advisor)
                print(f"  ✓ Danışman: {name} ({email})")

            await db.commit()
            print()
            print("=" * 50)
            print("KURULUM TAMAMLANDI")
            print("=" * 50)
            print(f"Ofis: {office_name}")
            print(f"Broker giriş: {broker_email} / {broker_password}")
            print(f"Danışman varsayılan şifre: Danisман123!")
            print()
            print("Danışmanlar ilk girişte şifrelerini değiştirmeli.")
            print("POST /api/v1/auth/change-password")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PropTech ilk kurulum seed scripti")
    parser.add_argument("--office", default="Çanakkale PropTech Emlak", help="Ofis / Şirket adı")
    parser.add_argument("--email", default="broker@proptech.com", help="Broker e-posta")
    parser.add_argument("--password", default="Broker2025!", help="Broker şifre")
    args = parser.parse_args()

    asyncio.run(seed(args.office, args.email, args.password))
