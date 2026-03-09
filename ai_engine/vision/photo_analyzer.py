"""
Görsel Şerefiye Puanlaması — GPT-4o Vision
Fotoğraflardan manzara, havuz, ankastre tespiti → m2 fiyatına % değer ekler.
"""
import os
from fastapi import APIRouter
from pydantic import BaseModel
import httpx

router = APIRouter(tags=["vision"])
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")


class PhotoAnalysisRequest(BaseModel):
    listing_id: str
    photo_urls: list[str]


class PhotoAnalysisResponse(BaseModel):
    listing_id: str
    visual_premium_pct: float    # m2 fiyatına eklenecek %
    photo_quality_score: float   # 0-1
    features: dict
    is_hidden_gem: bool          # Düşük kalite foto ama iyi konum


@router.post("/analyze-photos", response_model=PhotoAnalysisResponse)
async def analyze_photos(req: PhotoAnalysisRequest) -> PhotoAnalysisResponse:
    if not req.photo_urls or not OPENAI_KEY:
        return PhotoAnalysisResponse(
            listing_id=req.listing_id,
            visual_premium_pct=0.0,
            photo_quality_score=0.5,
            features={},
            is_hidden_gem=False,
        )

    prompt = (
        "Bu ev fotoğrafını analiz et. Sadece JSON döndür, başka hiçbir şey yazma:\n"
        '{"has_sea_view": bool, "has_pool": bool, "has_fireplace": bool, '
        '"has_builtin_kitchen": bool, "photo_quality": 0.0-1.0, "premium_pct": 0-30}'
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
            json={
                "model": "gpt-4o",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": req.photo_urls[0], "detail": "low"}},
                    ],
                }],
                "max_tokens": 150,
            },
            timeout=30,
        )

    import json
    result = {}
    try:
        content = response.json()["choices"][0]["message"]["content"]
        result = json.loads(content)
    except Exception:
        pass

    quality = result.get("photo_quality", 0.5)
    premium = result.get("premium_pct", 0.0)
    # Gizli cevher: fotoğraf kalitesi düşük ama konum/premium potansiyel yüksek
    is_hidden_gem = quality < 0.4 and premium > 10

    return PhotoAnalysisResponse(
        listing_id=req.listing_id,
        visual_premium_pct=premium,
        photo_quality_score=quality,
        features={
            "sea_view": result.get("has_sea_view", False),
            "pool": result.get("has_pool", False),
            "fireplace": result.get("has_fireplace", False),
            "builtin_kitchen": result.get("has_builtin_kitchen", False),
        },
        is_hidden_gem=is_hidden_gem,
    )
