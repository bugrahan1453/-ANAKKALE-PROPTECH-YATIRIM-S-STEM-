"""
Emsal Şelalesi ve Barometre
Yeni ilan fiyatını geçmiş kapanış fiyatlarıyla kıyaslar.
Yeşil (Fırsat) / Sarı (Normal) / Kırmızı (Şişirilmiş) sinyal üretir.
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["valuation"])


class BarometerRequest(BaseModel):
    listing_id: str
    price: float
    area_m2: float
    neighborhood: str
    room_count: str


class BarometerResponse(BaseModel):
    listing_id: str
    price_per_m2: float
    neighborhood_avg_per_m2: float
    deviation_pct: float          # + = şişirilmiş, - = ucuz
    signal: str                   # green | yellow | red
    label: str


@router.post("/barometer", response_model=BarometerResponse)
def run_barometer(req: BarometerRequest) -> BarometerResponse:
    price_per_m2 = req.price / req.area_m2 if req.area_m2 else 0

    # Gerçek uygulamada TimescaleDB'deki kapanış ilanlarından hesaplanır.
    # Bu placeholder değerleri production'da DB sorgusuyla değiştirilir.
    neighborhood_avg = _get_neighborhood_avg(req.neighborhood, req.room_count)
    deviation = ((price_per_m2 - neighborhood_avg) / neighborhood_avg) * 100 if neighborhood_avg else 0

    if deviation <= -10:
        signal, label = "green", "Fırsat — Emsalin %{:.0f} altında".format(abs(deviation))
    elif deviation >= 15:
        signal, label = "red", "Şişirilmiş — Emsalin %{:.0f} üstünde".format(deviation)
    else:
        signal, label = "yellow", "Normal piyasa fiyatı"

    return BarometerResponse(
        listing_id=req.listing_id,
        price_per_m2=round(price_per_m2),
        neighborhood_avg_per_m2=round(neighborhood_avg),
        deviation_pct=round(deviation, 1),
        signal=signal,
        label=label,
    )


def _get_neighborhood_avg(neighborhood: str, room_count: str) -> float:
    """
    Çanakkale ilçe/mahalle m² ortalama fiyatları (TL/m²).
    2025 Q1 piyasa verilerine dayanır; gerçek sistemde TimescaleDB'den güncellenir.
    """
    defaults: dict[str, float] = {
        # Merkez mahalleler
        "Kepez": 28_000, "Barbaros": 33_000, "Güzelyalı": 38_000,
        "Çanakkale Merkez": 31_000, "Fevzipaşa": 29_500, "İsmetpaşa": 27_000,
        "Cumhuriyet": 32_000, "Sarıcaeli": 26_000, "Hacımemet": 25_000,
        "Terzioğlu": 24_500, "Dardanos": 30_000, "Kalafat": 28_000,
        # İlçeler
        "Çan": 18_000, "Biga": 20_000, "Gelibolu": 22_000, "Lapseki": 19_500,
        "Ezine": 17_000, "Ayvacık": 16_000, "Bayramiç": 15_500,
        "Eceabat": 25_000, "Bozcaada": 55_000, "Gökçeada": 42_000, "Yenice": 14_000,
    }
    room_multipliers: dict[str, float] = {
        "1+1": 1.05, "2+1": 1.00, "3+1": 0.97, "4+1": 0.94, "5+1": 0.91,
    }
    base = defaults.get(neighborhood, 27_000)
    return base * room_multipliers.get(room_count, 1.0)
