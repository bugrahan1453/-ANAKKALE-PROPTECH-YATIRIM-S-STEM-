"""Görev API — Günlük danışman görev listesi, tele-prompter."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date, datetime, timezone

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.task import Task, TaskStatus
from app.models.user import User

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/today")
async def get_today_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Danışman için bugünün görev listesi — Sıfır inisiyatif."""
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    q = await db.execute(
        select(Task).where(
            and_(
                Task.tenant_id == current_user.tenant_id,
                Task.assigned_to_id == current_user.id,
                Task.status == TaskStatus.PENDING,
            )
        ).order_by(Task.priority.asc()).limit(10)
    )
    tasks = q.scalars().all()
    return [_serialize(t) for t in tasks]


@router.patch("/{task_id}/complete")
async def complete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = await db.execute(
        select(Task).where(Task.id == task_id, Task.assigned_to_id == current_user.id)
    )
    task = q.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    task.status = TaskStatus.DONE
    task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "ok"}


@router.get("/{task_id}/script")
async def get_task_script(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tele-prompter: Aranan mülkün durumuna göre konuşma senaryosu."""
    q = await db.execute(
        select(Task).where(Task.id == task_id, Task.assigned_to_id == current_user.id)
    )
    task = q.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    return {"script": task.script, "title": task.title}


def _serialize(t: Task) -> dict:
    return {
        "id": t.id,
        "task_type": t.task_type,
        "title": t.title,
        "priority": t.priority,
        "status": t.status,
        "listing_id": t.listing_id,
        "customer_id": t.customer_id,
        "due_date": t.due_date,
    }
