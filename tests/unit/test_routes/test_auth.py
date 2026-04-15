import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


async def test_login_with_valid_credentials_returns_token(client):
    response = await client.post(
        "/auth/token",
        json={"username": "demo", "password": "demo123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_with_invalid_credentials_returns_401(client):
    response = await client.post(
        "/auth/token",
        json={"username": "wrong", "password": "wrong"}
    )
    assert response.status_code == 401


async def test_prompts_endpoint_requires_auth(client):
    response = await client.get("/prompts")
    assert response.status_code == 401


async def test_prompts_endpoint_accessible_with_token(client):
    login = await client.post(
        "/auth/token",
        json={"username": "demo", "password": "demo123"}
    )
    token = login.json()["access_token"]

    response = await client.get(
        "/prompts",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "templates" in response.json()


async def test_prompts_returns_all_three_templates(client):
    login = await client.post(
        "/auth/token",
        json={"username": "demo", "password": "demo123"}
    )
    token = login.json()["access_token"]

    response = await client.get(
        "/prompts",
        headers={"Authorization": f"Bearer {token}"}
    )
    templates = response.json()["templates"]
    names = [t["name"] for t in templates]
    assert "planner" in names
    assert "coder" in names
    assert "summarizer" in names