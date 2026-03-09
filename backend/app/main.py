"""Çanakkale PropTech — FastAPI Ana Uygulama."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.endpoints import auth, listings, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Başlangıç: DB tablolarını oluştur (production'da Alembic kullan)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Kapanış
    await engine.dispose()


app = FastAPI(
    title="Çanakkale PropTech Yatırım Sistemi",
    description="Emlak zekası, AI değerleme ve broker otopilotu",
    version="1.0.0",
    docs_url="/api/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/api/redoc" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

# ─── MIDDLEWARE ───────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(o) for o in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── ROUTER ──────────────────────────────────────
app.include_router(auth.router, prefix="/api/v1")
app.include_router(listings.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "proptech-backend"}
