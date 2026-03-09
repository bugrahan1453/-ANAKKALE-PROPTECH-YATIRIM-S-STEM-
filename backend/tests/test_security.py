"""Güvenlik — Şifreleme, JWT, RBAC testleri."""
import pytest
from app.core.security import hash_password, verify_password, create_token, decode_token, encrypt_field, decrypt_field
from jose import JWTError


def test_password_hash_and_verify():
    password = "G@v3nliSifre123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("yanlis_sifre", hashed)


def test_jwt_create_and_decode():
    payload = {"sub": "user-123", "tenant_id": "tenant-abc", "role": "broker"}
    token = create_token(payload)
    decoded = decode_token(token)
    assert decoded["sub"] == "user-123"
    assert decoded["tenant_id"] == "tenant-abc"


def test_jwt_invalid_token():
    with pytest.raises(JWTError):
        decode_token("gecersiz.token.burada")


def test_field_encryption():
    original = "05XX XXX XX XX"
    encrypted = encrypt_field(original)
    assert encrypted != original
    decrypted = decrypt_field(encrypted)
    assert decrypted == original


def test_field_encryption_empty():
    assert encrypt_field("") == ""
    assert decrypt_field("") == ""


def test_field_encryption_none():
    assert encrypt_field(None) is None
    assert decrypt_field(None) is None
