# Çanakkale PropTech — Sunucu Kurulum Rehberi

## Hangi Sunucu Lazım?

### Minimum (Başlangıç — Tek Ofis)
| Kaynak | Değer |
|--------|-------|
| CPU | 4 vCPU |
| RAM | 8 GB |
| Disk | 80 GB SSD |
| Bant Genişliği | Sınırsız |
| **Tahmini Aylık Maliyet** | **~$40-60 (DigitalOcean/Hetzner)** |

### Önerilen (Aktif Kullanım — Scraper + AI)
| Kaynak | Değer |
|--------|-------|
| CPU | 8 vCPU |
| RAM | 16 GB |
| Disk | 160 GB SSD |
| **Tahmini Aylık Maliyet** | **~$80-120** |

### Ölçeklenmiş (Çok Ofis / SaaS Satışı)
- Kubernetes (k3s) üzerinde her servis ayrı pod
- Managed PostgreSQL (Supabase veya Neon.tech)
- Cloudflare CDN + WAF
- **Tahmini: $200-400/ay**

---

## Önerilen Sağlayıcı: Hetzner Cloud (En Ucuz/Güvenilir)

### Adım 1 — Sunucu Oluştur
```
Hetzner Cloud → New Server
Konum: Falkenstein (EU) veya Helsinki
Tip: CPX31 (4 vCPU, 8 GB RAM) → ~$16/ay
İşletim Sistemi: Ubuntu 22.04 LTS
```

### Adım 2 — Temel Güvenlik
```bash
# Root olarak giriş yap, sonra:
apt update && apt upgrade -y

# Güvenlik duvarı
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable

# SSH anahtar girişi (şifre girişini kapat)
nano /etc/ssh/sshd_config
# → PasswordAuthentication no
systemctl restart sshd

# Fail2ban (brute force koruması)
apt install fail2ban -y
systemctl enable fail2ban
```

### Adım 3 — Docker Kurulumu
```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
usermod -aG docker $USER

# Docker Compose
apt install docker-compose-plugin -y
```

### Adım 4 — Projeyi Sunucuya Al
```bash
cd /opt
git clone https://github.com/SENİN-KULLANICI-ADIN/canakkale-proptech.git
cd canakkale-proptech

# .env dosyasını oluştur
cp .env.example .env
nano .env   # Değişkenleri doldur
```

### Adım 5 — SSL Sertifikası (Let's Encrypt)
```bash
# nginx/conf.d/proptech.conf içinde DOMAIN.com'u kendi domain'inle değiştir
sed -i 's/DOMAIN.com/senin-domain.com/g' nginx/conf.d/proptech.conf

# Önce HTTP ile başlat (certbot için)
docker compose up -d nginx certbot

# Sertifika al
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d senin-domain.com -d www.senin-domain.com -d api.senin-domain.com \
  --email email@example.com --agree-tos --no-eff-email
```

### Adım 6 — Tüm Servisleri Başlat
```bash
docker compose up -d

# Durumu kontrol et
docker compose ps
docker compose logs -f backend
```

### Adım 7 — Veritabanı Başlangıcı
```bash
# TimescaleDB hypertable'ı oluştur (tek seferlik)
docker compose exec postgres psql -U proptech -d proptech -c \
  "SELECT create_hypertable('listing_price_history', 'recorded_at', if_not_exists => TRUE);"
```

---

## Servis Mimarisi (Portlar)

```
İnternet
    │
    ▼
[Nginx :80/:443]  ← SSL termination, rate limiting
    ├── / → [Next.js Frontend :3000]
    └── /api/ → [FastAPI Backend :8000]
                    │
                    ├── [PostgreSQL/TimescaleDB :5432]
                    ├── [Redis :6379]
                    ├── [Celery Worker] ← Arka plan görevleri
                    ├── [Celery Beat]   ← Zamanlanmış görevler
                    ├── [Scraper :8001] ← Playwright scraping
                    └── [AI Engine :8002] ← GPT-4o Vision, NLP
```

---

## Monitoring (İzleme)

### Flower — Celery İş Kuyruğu Monitörü
```bash
# http://sunucu-ip:5555 adresinden erişilir
docker compose exec celery_worker celery -A app.workers.celery_app flower
```

### Logları takip et
```bash
docker compose logs -f --tail=100 backend
docker compose logs -f --tail=100 scraper
docker compose logs -f --tail=100 celery_worker
```

---

## Proxy Servisi (Scraper için)
Sahibinden.com bot korumasını aşmak için **residential proxy** gereklidir.

Önerilen sağlayıcılar (ücretli):
- **Smartproxy** — ~$75/ay (100 GB)
- **Brightdata** — ~$500/ay (profesyonel)
- **Webshare** — ~$30/ay (başlangıç için)

`.env` dosyasında `PROXY_API_KEY` değişkenini doldurun.

---

## Yedekleme

```bash
# PostgreSQL otomatik yedek (günlük cron)
crontab -e
# Ekle:
# 0 3 * * * docker compose exec -T postgres pg_dump -U proptech proptech | gzip > /opt/backups/db_$(date +\%Y\%m\%d).sql.gz
```

---

## Tahmini Aylık Maliyet Özeti

| Kalem | Maliyet |
|-------|---------|
| Hetzner CPX31 Sunucu | ~$16 |
| Domain + SSL (Let's Encrypt) | Ücretsiz |
| Residential Proxy (Webshare) | ~$30 |
| OpenAI API (GPT-4o Vision) | ~$20-50 |
| Twilio SMS/WhatsApp | ~$5-10 |
| **TOPLAM** | **~$70-110/ay** |
