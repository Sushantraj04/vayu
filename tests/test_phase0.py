import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_and_ready_endpoints(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"

    resp_ready = await async_client.get("/api/v1/ready")
    assert resp_ready.status_code in [200, 503]
    ready_data = resp_ready.json()
    assert "database" in ready_data
    assert "redis" in ready_data


@pytest.mark.asyncio
async def test_auth_login_success_and_failure(async_client: AsyncClient):
    bad_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@vayu-net.org",
        "password": "WrongPassword!"
    })
    assert bad_resp.status_code == 401

    good_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@vayu-net.org",
        "password": "AdminPassword123!"
    })
    assert good_resp.status_code == 200
    token_data = good_resp.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["role"] == "admin"
    assert token_data["token_type"] == "bearer"

    token = token_data["access_token"]
    me_resp = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "admin@vayu-net.org"
    assert me_data["role"] == "admin"


@pytest.mark.asyncio
async def test_rbac_access_control(async_client: AsyncClient):
    anon_resp = await async_client.get("/api/v1/users/")
    assert anon_resp.status_code == 401

    citizen_login = await async_client.post("/api/v1/auth/login", json={
        "email": "citizen@vayu-net.org",
        "password": "CitizenPassword123!"
    })
    citizen_token = citizen_login.json()["access_token"]
    forbidden_resp = await async_client.get("/api/v1/users/", headers={"Authorization": f"Bearer {citizen_token}"})
    assert forbidden_resp.status_code == 403

    admin_login = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@vayu-net.org",
        "password": "AdminPassword123!"
    })
    admin_token = admin_login.json()["access_token"]
    admin_resp = await async_client.get("/api/v1/users/", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_resp.status_code == 200
    users_list = admin_resp.json()
    assert len(users_list) >= 2


@pytest.mark.asyncio
async def test_corridors_api(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/corridors/")
    assert resp.status_code == 200
    corridors = resp.json()
    assert len(corridors) >= 2
    corridor_ids = [c["id"] for c in corridors]
    assert "indo-gangetic-main" in corridor_ids
    assert "delhi-ncr-industrial" in corridor_ids

    summary_resp = await async_client.get("/api/v1/corridors/indo-gangetic-main/summary")
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()
    assert "risk_index" in summary_data
    assert 0 <= summary_data["risk_index"] <= 100
    assert "nodes" in summary_data
    assert len(summary_data["nodes"]) == 6


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/metrics")
    assert resp.status_code == 200
    assert "vayunet_http_requests_total" in resp.text
