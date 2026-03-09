"""AI Görevleri — Motivasyon skoru, görsel analiz, DOM güncelleme."""
from app.workers.celery_app import celery_app
import logging
import re

logger = logging.getLogger(__name__)

# Türkçe motivasyon tetikleyicileri
MOTIVATION_KEYWORDS = {
    "acil": 30, "borçtan": 25, "öğlene kadar": 40, "kredi uygun değil": 20,
    "tayin nedeniyle": 25, "mecbur": 20, "yurt dışı": 15, "icra": 35,
    "hızlı": 10, "bu hafta": 15, "fiyat düşer": 10, "pazarlık": 5,
    "iflas": 40, "anlaşılır": 5, "acele": 20,
}


@celery_app.task(name="app.workers.tasks.ai_tasks.score_motivation")
def score_motivation(listing_id: str, description: str) -> int:
    """İlan açıklamasından satıcı motivasyon skoru hesapla (1-100)."""
    if not description:
        return 1
    desc_lower = description.lower()
    score = 1
    for keyword, weight in MOTIVATION_KEYWORDS.items():
        if keyword in desc_lower:
            score += weight
    score = min(score, 100)
    logger.info(f"Listing {listing_id} motivation score: {score}")
    # Gerçek uygulamada DB'ye kaydet
    return score


@celery_app.task(name="app.workers.tasks.ai_tasks.analyze_photos")
def analyze_photos(listing_id: str, photo_urls: list[str]) -> dict:
    """
    Görsel şerefiye analizi:
    - Manzara (Boğaz/Deniz) tespiti
    - Havuz, şömine, ankastre tespiti
    - Fotoğraf kalite puanı
    """
    try:
        from openai import OpenAI
        from app.core.config import settings

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        if not photo_urls:
            return {"visual_premium": 0.0, "quality_score": 0.5, "features": {}}

        # İlk fotoğrafı analiz et (maliyet optimizasyonu)
        first_photo = photo_urls[0]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": (
                        "Bu ev fotoğrafını analiz et. JSON formatında yanıt ver:\n"
                        "{\n"
                        '  "has_sea_view": bool,\n'
                        '  "has_pool": bool,\n'
                        '  "has_fireplace": bool,\n'
                        '  "has_builtin_kitchen": bool,\n'
                        '  "photo_quality": 0-1 (0=karanlık/kötü, 1=profesyonel),\n'
                        '  "premium_pct": 0-30 (m2 fiyatına eklenecek % şerefiye)\n'
                        "}"
                    )},
                    {"type": "image_url", "image_url": {"url": first_photo}},
                ],
            }],
            max_tokens=200,
        )

        import json
        result = json.loads(response.choices[0].message.content)
        return {
            "visual_premium": result.get("premium_pct", 0),
            "quality_score": result.get("photo_quality", 0.5),
            "features": {
                "sea_view": result.get("has_sea_view", False),
                "pool": result.get("has_pool", False),
                "fireplace": result.get("has_fireplace", False),
                "builtin_kitchen": result.get("has_builtin_kitchen", False),
            },
        }
    except Exception as e:
        logger.error(f"Fotoğraf analizi başarısız: {e}")
        return {"visual_premium": 0.0, "quality_score": 0.5, "features": {}}


@celery_app.task(name="app.workers.tasks.ai_tasks.update_dom_counters")
def update_dom_counters():
    """Gece yarısı aktif ilanların DOM sayacını 1 artır."""
    # Gerçek uygulamada DB bağlantısıyla çalışır
    logger.info("DOM sayaçları güncelleniyor...")


@celery_app.task(name="app.workers.tasks.ai_tasks.calculate_arv")
def calculate_arv(listing_id: str, neighborhood: str, area_m2: float, current_price: float) -> dict:
    """
    ARV (After Repair Value) hesapla:
    O mahalledeki yenilenmiş evlerin ort. m2 fiyatı * alan - tahmini tadilat masrafı
    """
    # Ortalama tadilat maliyeti (Çanakkale 2024 verileri)
    renovation_cost_per_m2 = 8000  # TL/m2
    estimated_renovation = area_m2 * renovation_cost_per_m2

    # Bu değer gerçekte DB'deki mahalle istatistiklerinden gelir
    avg_renovated_price_per_m2 = 35000  # TL/m2 (placeholder)
    arv = area_m2 * avg_renovated_price_per_m2
    net_profit = arv - current_price - estimated_renovation

    return {
        "arv": arv,
        "renovation_cost": estimated_renovation,
        "net_profit": net_profit,
        "roi_pct": (net_profit / (current_price + estimated_renovation)) * 100 if current_price > 0 else 0,
    }
