"""AI Engine — Değerleme, NLP, Computer Vision REST API."""
from fastapi import FastAPI
from valuation.price_barometer import router as barometer_router
from nlp.motivation_scorer import router as motivation_router
from vision.photo_analyzer import router as vision_router

app = FastAPI(title="PropTech AI Engine")

app.include_router(barometer_router, prefix="/ai/valuation")
app.include_router(motivation_router, prefix="/ai/nlp")
app.include_router(vision_router, prefix="/ai/vision")


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-engine"}
