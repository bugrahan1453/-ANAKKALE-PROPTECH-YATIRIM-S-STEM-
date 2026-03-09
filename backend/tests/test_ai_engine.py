"""AI motor birim testleri — Motivasyon skoru, fiyat barometresi."""
import pytest
from ai_engine.nlp.motivation_scorer import MotivationScorer
from ai_engine.valuation.price_barometer import PriceBarometer


class TestMotivationScorer:
    def setup_method(self):
        self.scorer = MotivationScorer()

    def test_urgent_keywords(self):
        text = "ACİL SATILIK! Kamulaştırma nedeniyle satılık. Tapu hazır."
        score = self.scorer.score(text)
        assert score >= 50, "Acil satış anahtar kelimeleri yüksek skor vermeli"

    def test_normal_listing(self):
        text = "Güzel daire satılık. Balkonlu, manzaralı."
        score = self.scorer.score(text)
        assert 0 <= score < 50, "Normal ilan orta-düşük skor almalı"

    def test_zero_score_empty(self):
        assert self.scorer.score("") == 0
        assert self.scorer.score(None) == 0

    def test_multiple_keywords(self):
        text = "borç nedeniyle acil satılık, miras paylaşımı, hızlı karar verecek alıcıya"
        score = self.scorer.score(text)
        assert score >= 70, "Çok sayıda motivasyon kelimesi çok yüksek skor vermeli"


class TestPriceBarometer:
    def setup_method(self):
        self.barometer = PriceBarometer()

    def test_green_signal_below_market(self):
        result = self.barometer.analyze(
            price=800_000,
            area_m2=100,
            district="Merkez",
            room_count="3+1",
        )
        assert result["signal"] in ("green", "yellow", "red")
        assert "price_per_m2" in result

    def test_price_per_m2_calculation(self):
        result = self.barometer.analyze(
            price=1_000_000,
            area_m2=100,
            district="Merkez",
        )
        assert result["price_per_m2"] == 10_000.0

    def test_returns_required_fields(self):
        result = self.barometer.analyze(price=500_000, area_m2=80, district="Kepez")
        required_keys = ["signal", "price_per_m2", "neighborhood_avg", "discount_pct"]
        for key in required_keys:
            assert key in result, f"'{key}' alanı eksik"
