"""Elasticsearch Full-text Arama — İlan açıklamalarında hızlı metin arama."""
from fastapi import APIRouter, Depends, Query
import httpx
import logging

from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/search", tags=["search"])
logger = logging.getLogger(__name__)

ES_URL = "http://elasticsearch:9200"
INDEX_NAME = "listings"


@router.get("/")
async def search_listings(
    q: str = Query(..., min_length=2),
    district: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """İlan başlık ve açıklamalarında full-text arama."""
    must_clauses = [
        {"multi_match": {"query": q, "fields": ["title^3", "description", "neighborhood^2"], "fuzziness": "AUTO"}},
        {"term": {"tenant_id": current_user.tenant_id}},
    ]
    if district:
        must_clauses.append({"term": {"district": district}})

    body = {
        "query": {"bool": {"must": must_clauses}},
        "from": (page - 1) * size,
        "size": size,
        "sort": [{"_score": "desc"}, {"motivation_score": {"order": "desc", "missing": "_last"}}],
        "highlight": {"fields": {"title": {}, "description": {"fragment_size": 150, "number_of_fragments": 2}}},
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{ES_URL}/{INDEX_NAME}/_search", json=body, timeout=10)

        if response.status_code != 200:
            return {"total": 0, "items": [], "error": "Arama servisi kullanılamıyor"}

        data = response.json()
        hits = data.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        items = [
            {
                **hit["_source"],
                "score": hit["_score"],
                "highlights": hit.get("highlight", {}),
            }
            for hit in hits.get("hits", [])
        ]
        return {"total": total, "page": page, "size": size, "items": items}

    except Exception as e:
        logger.error(f"Elasticsearch arama hatası: {e}")
        return {"total": 0, "items": [], "error": str(e)}


@router.post("/index/{listing_id}")
async def index_listing(listing_id: str, listing_data: dict):
    """Yeni ilanı Elasticsearch'e indexle (internal)."""
    try:
        async with httpx.AsyncClient() as client:
            await client.put(
                f"{ES_URL}/{INDEX_NAME}/_doc/{listing_id}",
                json=listing_data,
                timeout=10,
            )
        return {"status": "indexed"}
    except Exception as e:
        logger.error(f"İndeksleme hatası: {e}")
        return {"status": "error", "detail": str(e)}


@router.post("/create-index")
async def create_index():
    """Elasticsearch index'ini oluştur (tek seferlik)."""
    mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text", "analyzer": "turkish"},
                "description": {"type": "text", "analyzer": "turkish"},
                "district": {"type": "keyword"},
                "neighborhood": {"type": "text", "analyzer": "turkish", "fields": {"keyword": {"type": "keyword"}}},
                "tenant_id": {"type": "keyword"},
                "price": {"type": "float"},
                "area_m2": {"type": "float"},
                "room_count": {"type": "keyword"},
                "source_site": {"type": "keyword"},
                "is_fsbo": {"type": "boolean"},
                "status": {"type": "keyword"},
                "motivation_score": {"type": "integer"},
                "price_signal": {"type": "keyword"},
                "days_on_market": {"type": "integer"},
            }
        },
        "settings": {
            "analysis": {
                "analyzer": {
                    "turkish": {"type": "custom", "tokenizer": "standard", "filter": ["lowercase", "turkish_stemmer"]},
                },
                "filter": {
                    "turkish_stemmer": {"type": "stemmer", "language": "turkish"},
                },
            }
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{ES_URL}/{INDEX_NAME}", json=mapping, timeout=10)
        return {"status": "created", "response": response.json()}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
