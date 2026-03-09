"""Kurtlar Vadisi Oyunlaştırması — Leaderboard & ödül sistemi."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from datetime import date, datetime, timezone

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole
from app.schemas.task import LeaderboardEntry

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Günlük danışman performans sıralaması."""
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)

    # Her danışmanın bugün tamamladığı görev sayısını hesapla
    q = await db.execute(
        select(
            User.id,
            User.full_name,
            func.count(case((Task.task_type == "cold_call", 1))).label("calls"),
            func.count(case((Task.task_type == "showing", 1))).label("appointments"),
            func.count(Task.id).label("total"),
        )
        .join(Task, and_(Task.assigned_to_id == User.id, Task.status == TaskStatus.DONE))
        .where(
            and_(
                User.tenant_id == current_user.tenant_id,
                User.role == UserRole.ADVISOR,
                User.is_active == True,
                Task.completed_at >= today_start,
            )
        )
        .group_by(User.id, User.full_name)
        .order_by(func.count(Task.id).desc())
    )

    rows = q.all()
    result = []
    for rank, row in enumerate(rows, 1):
        calls = row.calls or 0
        appointments = row.appointments or 0
        score = calls * 10 + appointments * 25 + (row.total or 0) * 5
        result.append(LeaderboardEntry(
            advisor_id=row.id,
            advisor_name=row.full_name,
            calls_today=calls,
            appointments_today=appointments,
            deals_this_month=0,  # Ayrı bir sorgu ile hesaplanır
            score=score,
            rank=rank,
        ))

    return result


@router.get("/rewards")
async def get_available_rewards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hedefini tutturan danışmanlar için ödül portföyleri."""
    return {
        "daily_call_target": 15,
        "daily_appointment_target": 3,
        "reward_description": "Günlük hedefini tutturan danışmana, en sıcak lead portföyü otomatik atanır",
        "top_advisor": None,  # Gün sonunda hesaplanır
    }
