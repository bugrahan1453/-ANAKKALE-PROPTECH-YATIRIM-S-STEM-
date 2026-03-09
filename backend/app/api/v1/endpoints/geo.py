"""Saha Rotası (Geo-Routing) ve Mahalle Görevleri."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.config import settings
from app.models.listing import Listing
from app.models.user import User

router = APIRouter(prefix="/geo", tags=["geo"])


@router.post("/optimize-route")
async def optimize_route(
    listing_ids: list[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    3+ ev gösterimi için en kısa sürüş rotasını hesapla.
    Google Maps Directions API kullanır.
    """
    q = await db.execute(
        select(Listing).where(
            and_(
                Listing.id.in_(listing_ids),
                Listing.tenant_id == current_user.tenant_id,
            )
        )
    )
    listings = q.scalars().all()

    # Koordinatları topla
    waypoints = []
    for listing in listings:
        if listing.latitude and listing.longitude:
            waypoints.append({
                "listing_id": listing.id,
                "title": listing.title,
                "lat": listing.latitude,
                "lng": listing.longitude,
                "address": listing.address_raw,
            })

    if len(waypoints) < 2:
        return {"route": waypoints, "total_distance_km": 0, "total_duration_min": 0}

    # Google Maps Directions API
    optimized = await _google_directions(waypoints)
    return optimized


@router.get("/nearby-tasks")
async def get_nearby_tasks(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(2.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Danışmanın mevcut konumuna yakın gösterim/görev listesi.
    Çevrimdışı GPS görevleri dahil.
    """
    # PostgreSQL'de basit mesafe hesabı (tam formül Haversine)
    # Yaklaşık: 1 derece ≈ 111 km
    delta = radius_km / 111.0
    q = await db.execute(
        select(Listing).where(
            and_(
                Listing.tenant_id == current_user.tenant_id,
                Listing.latitude.between(lat - delta, lat + delta),
                Listing.longitude.between(lng - delta, lng + delta),
            )
        ).limit(20)
    )
    listings = q.scalars().all()
    return {
        "center": {"lat": lat, "lng": lng},
        "radius_km": radius_km,
        "count": len(listings),
        "items": [
            {
                "id": l.id,
                "title": l.title,
                "lat": l.latitude,
                "lng": l.longitude,
                "price": l.price,
                "district": l.district,
            }
            for l in listings
        ],
    }


async def _google_directions(waypoints: list[dict]) -> dict:
    """Google Maps Directions API ile rota optimizasyonu."""
    import httpx

    if not settings.GOOGLE_MAPS_API_KEY:
        return {
            "route": waypoints,
            "total_distance_km": 0,
            "total_duration_min": 0,
            "maps_url": "",
            "note": "Google Maps API key yapılandırılmamış",
        }

    origin = f"{waypoints[0]['lat']},{waypoints[0]['lng']}"
    destination = f"{waypoints[-1]['lat']},{waypoints[-1]['lng']}"
    wp_str = "|".join(f"{w['lat']},{w['lng']}" for w in waypoints[1:-1])

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params={
                "origin": origin,
                "destination": destination,
                "waypoints": f"optimize:true|{wp_str}" if wp_str else "",
                "key": settings.GOOGLE_MAPS_API_KEY,
                "language": "tr",
            },
            timeout=15,
        )

    data = response.json()
    if data.get("status") != "OK":
        return {"route": waypoints, "total_distance_km": 0, "total_duration_min": 0}

    route = data["routes"][0]
    total_distance = sum(leg["distance"]["value"] for leg in route["legs"])
    total_duration = sum(leg["duration"]["value"] for leg in route["legs"])

    return {
        "route": waypoints,
        "optimized_order": route.get("waypoint_order", []),
        "total_distance_km": round(total_distance / 1000, 1),
        "total_duration_min": round(total_duration / 60),
        "maps_url": f"https://www.google.com/maps/dir/{'/'.join(f'{w['lat']},{w['lng']}' for w in waypoints)}",
    }
