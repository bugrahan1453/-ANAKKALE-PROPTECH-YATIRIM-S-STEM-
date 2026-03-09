from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List
import secrets


class Settings(BaseSettings):
    # Uygulama
    APP_ENV: str = "production"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Veritabanı
    DATABASE_URL: str
    REDIS_URL: str

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []

    # Şifreleme
    ENCRYPTION_KEY: str = ""

    # AI
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # SMS / WhatsApp
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    BROKER_PHONE_NUMBER: str = ""

    # E-posta
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # Scraper
    PROXY_API_KEY: str = ""
    SCRAPE_INTERVAL_MINUTES: int = 30

    # Arama (Elasticsearch)
    ELASTICSEARCH_URL: str = "http://elasticsearch:9200"
    ELASTICSEARCH_INDEX: str = "listings"

    # Harita
    GOOGLE_MAPS_API_KEY: str = ""
    TKGM_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
