"""Satıcı Motivasyon Skoru — Türkçe NLP ile 1-100 puan."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["nlp"])

KEYWORD_WEIGHTS = {
    "acil": 30, "borçtan": 25, "öğlene kadar": 40, "kredi uygun değil": 20,
    "tayin nedeniyle": 25, "mecbur": 20, "yurt dışı": 15, "icra": 35,
    "hızlı": 10, "bu hafta": 15, "anlaşılır": 5, "acele": 20,
    "satılık": 2, "tercihen": 3, "fiyat düşer": 10, "pazarlık": 5,
}


class MotivationRequest(BaseModel):
    listing_id: str
    description: str


class MotivationResponse(BaseModel):
    listing_id: str
    score: int  # 1-100
    triggered_keywords: list[str]


@router.post("/motivation-score", response_model=MotivationResponse)
def score_motivation(req: MotivationRequest) -> MotivationResponse:
    desc = req.description.lower()
    score = 1
    triggered = []
    for kw, weight in KEYWORD_WEIGHTS.items():
        if kw in desc:
            score += weight
            triggered.append(kw)
    return MotivationResponse(
        listing_id=req.listing_id,
        score=min(score, 100),
        triggered_keywords=triggered,
    )
