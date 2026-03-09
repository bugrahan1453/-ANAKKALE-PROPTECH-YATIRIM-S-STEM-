"""Portföy API — İlan atamaları, yeniden atama, özel portföy."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.deps import get_current_user, require_broker
from app.models.portfolio import Portfolio
from app.models.user import User, UserRole
from app.schemas.portfolio import PortfolioCreate, PortfolioOut, PortfolioReassign

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("/")
async def list_portfolios(
    advisor_id: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = [Portfolio.tenant_id == current_user.tenant_id]
    if current_user.role == UserRole.ADVISOR:
        filters.append(Portfolio.advisor_id == current_user.id)
    elif advisor_id:
        filters.append(Portfolio.advisor_id == advisor_id)

    q = await db.execute(
        select(Portfolio).where(and_(*filters))
        .order_by(Portfolio.assigned_at.desc())
        .offset((page - 1) * size).limit(size)
    )
    return q.scalars().all()


@router.post("/", status_code=201)
async def assign_portfolio(
    payload: PortfolioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    portfolio = Portfolio(
        tenant_id=current_user.tenant_id,
        listing_id=payload.listing_id,
        advisor_id=payload.advisor_id,
        notes=payload.notes,
        is_exclusive=payload.is_exclusive,
    )
    db.add(portfolio)
    await db.flush()
    await db.refresh(portfolio)
    return portfolio


@router.patch("/{portfolio_id}/reassign")
async def reassign_portfolio(
    portfolio_id: str,
    payload: PortfolioReassign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    q = await db.execute(
        select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.tenant_id == current_user.tenant_id,
        )
    )
    portfolio = q.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portföy bulunamadı")

    portfolio.advisor_id = payload.new_advisor_id
    await db.flush()
    return {"status": "ok", "new_advisor_id": payload.new_advisor_id}


@router.delete("/{portfolio_id}", status_code=204)
async def remove_portfolio(
    portfolio_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    q = await db.execute(
        select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.tenant_id == current_user.tenant_id,
        )
    )
    portfolio = q.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portföy bulunamadı")
    await db.delete(portfolio)
    await db.flush()
