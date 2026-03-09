from pydantic import BaseModel
from datetime import datetime


class TaskOut(BaseModel):
    id: str
    task_type: str
    title: str
    script: str | None = None
    priority: int
    status: str
    listing_id: str | None = None
    customer_id: str | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None
    is_ai_generated: bool

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    task_type: str
    title: str
    script: str | None = None
    priority: int = 5
    listing_id: str | None = None
    customer_id: str | None = None
    assigned_to_id: str | None = None
    due_date: datetime | None = None


class VoiceNoteRequest(BaseModel):
    audio_base64: str
    format: str = "webm"


class VoiceNoteResponse(BaseModel):
    transcript: str
    extracted_data: dict  # budget, rooms, district vb.
    customer_id: str | None = None


class LeaderboardEntry(BaseModel):
    advisor_id: str
    advisor_name: str
    calls_today: int
    appointments_today: int
    deals_this_month: int
    score: int
    rank: int
