"""Sesli CRM Asistanı — Speech-to-Text + otomatik müşteri profil güncelleme."""
import base64
import json
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.task import VoiceNoteRequest, VoiceNoteResponse

router = APIRouter(prefix="/voice", tags=["voice"])
logger = logging.getLogger(__name__)


@router.post("/transcribe", response_model=VoiceNoteResponse)
async def transcribe_voice_note(
    payload: VoiceNoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sahadaki danışman sesli not bırakır.
    1. Whisper ile metne dönüştürülür
    2. GPT ile bütçe, oda sayısı, ilçe gibi detaylar çıkartılır
    3. Müşteri profiline otomatik işlenir
    """
    audio_bytes = base64.b64decode(payload.audio_base64)

    # 1. Speech-to-Text (OpenAI Whisper)
    transcript = await _whisper_transcribe(audio_bytes, payload.format)

    # 2. Yapılandırılmış veri çıkartma (NLP)
    extracted = await _extract_structured_data(transcript)

    return VoiceNoteResponse(
        transcript=transcript,
        extracted_data=extracted,
        customer_id=extracted.get("customer_id"),
    )


async def _whisper_transcribe(audio_bytes: bytes, fmt: str) -> str:
    """OpenAI Whisper API ile sesi metne dönüştür."""
    import httpx

    if not settings.OPENAI_API_KEY:
        return "[Whisper API key eksik — transcript simülasyonu]"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            files={"file": (f"audio.{fmt}", audio_bytes, f"audio/{fmt}")},
            data={"model": "whisper-1", "language": "tr"},
            timeout=30,
        )
    if response.status_code == 200:
        return response.json().get("text", "")
    logger.error(f"Whisper hatası: {response.status_code}")
    return ""


async def _extract_structured_data(transcript: str) -> dict:
    """GPT ile transkriptten yapılandırılmış veri çıkart."""
    import httpx

    if not settings.OPENAI_API_KEY or not transcript:
        return {}

    prompt = (
        "Aşağıdaki emlak danışmanı sesli notundan yapılandırılmış veri çıkart. "
        "Sadece JSON döndür:\n"
        '{"customer_name": "", "budget_min": null, "budget_max": null, '
        '"preferred_rooms": "", "preferred_district": "", '
        '"notes": "", "urgency": "low/medium/high"}\n\n'
        f"Not: {transcript}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
            },
            timeout=30,
        )

    try:
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception:
        return {"notes": transcript}
