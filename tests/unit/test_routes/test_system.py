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


async def test_health_check_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_health_check_returns_version(client):
    response = await client.get("/health")
    assert "version" in response.json()


async def test_health_check_includes_trace_id_header(client):
    response = await client.get("/health")
    assert "x-trace-id" in response.headers