-- ════════════════════════════════════════════════════
-- ÇANAKKALE PROPTECH — Veritabanı Başlangıç Scripti
-- TimescaleDB extension + Row-Level Security (RLS)
-- ════════════════════════════════════════════════════

-- TimescaleDB eklentisini etkinleştir
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ─────────────────────────────────────────────────────
-- listing_price_history TabloSunu TimescaleDB Hypertable'a Dönüştür
-- (SQLAlchemy create_all çalıştıktan SONRA çalışır)
-- ─────────────────────────────────────────────────────
-- Bu komut uygulama ilk başladığında manuel çalıştırılmalı:
-- SELECT create_hypertable('listing_price_history', 'recorded_at', if_not_exists => TRUE);

-- ─────────────────────────────────────────────────────
-- ROW-LEVEL SECURITY (RLS) — Multi-tenant izolasyonu
-- ─────────────────────────────────────────────────────

-- listings tablosu için RLS
ALTER TABLE IF EXISTS listings ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_listings ON listings;
CREATE POLICY tenant_isolation_listings ON listings
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::text);

-- customers tablosu için RLS
ALTER TABLE IF EXISTS customers ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_customers ON customers;
CREATE POLICY tenant_isolation_customers ON customers
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::text);

-- tasks tablosu için RLS
ALTER TABLE IF EXISTS tasks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_tasks ON tasks;
CREATE POLICY tenant_isolation_tasks ON tasks
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::text);

-- portfolios tablosu için RLS
ALTER TABLE IF EXISTS portfolios ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_portfolios ON portfolios;
CREATE POLICY tenant_isolation_portfolios ON portfolios
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::text);

-- ─────────────────────────────────────────────────────
-- İNDEKSLER — Sık sorgulanan alanlar
-- ─────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_listings_district ON listings(district);
CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price);
CREATE INDEX IF NOT EXISTS idx_listings_motivation ON listings(motivation_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_listings_source ON listings(source_site, source_id);
CREATE INDEX IF NOT EXISTS idx_listings_status_tenant ON listings(status, tenant_id);
CREATE INDEX IF NOT EXISTS idx_listings_photo_hash ON listings(photo_hash);
CREATE INDEX IF NOT EXISTS idx_listings_address_hash ON listings(address_hash);
