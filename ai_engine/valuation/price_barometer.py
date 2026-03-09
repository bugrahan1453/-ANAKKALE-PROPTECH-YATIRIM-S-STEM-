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
    """Placeholder — production'da DB sorgusu ile değiştirilir."""
    defaults = {
        "Kepez": 28000, "Barbaros": 32000, "Güzelyalı": 35000,
        "Çanakkale Merkez": 30000,
    }
    return defaults.get(neighborhood, 29000)
