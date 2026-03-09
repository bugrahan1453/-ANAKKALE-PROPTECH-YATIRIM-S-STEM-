from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from app.core.config import settings
import base64

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY
    if not key:
        key = Fernet.generate_key().decode()
    # Fernet key 32 url-safe base64 byte ister
    padded = (key + "=" * (44 - len(key) % 44)).encode()[:44]
    return Fernet(base64.urlsafe_b64encode(base64.urlsafe_b64decode(padded + b"==")))


def encrypt_field(value: str) -> str:
    """Telefon numarası gibi hassas alanları şifrele."""
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_field(token: str) -> str:
    return _get_fernet().decrypt(token.encode()).decode()
