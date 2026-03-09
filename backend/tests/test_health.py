"""Temel sağlık ve auth testleri."""
import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_wrong_credentials(client):
    response = await client.post("/api/v1/auth/login", data={
        "username": "yanlis@test.com",
        "password": "yanlis_sifre",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_no_token(client):
    response = await client.get("/api/v1/listings/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_docs_available(client):
    response = await client.get("/api/docs")
    assert response.status_code == 200
