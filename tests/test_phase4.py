import pytest
import numpy as np
from httpx import AsyncClient

from backend.app.federated.privacy import DifferentialPrivacyEngine
from backend.app.federated.aggregator import FedAvgCoordinator
from backend.app.federated.client import FederatedNodeClient
from backend.app.core.config import settings


# ==============================================================================
# 1. Differential Privacy & FedAvg Mathematical Unit Tests
# ==============================================================================

def test_differential_privacy_clipping_and_noise():
    clip_norm = 1.5
    epsilon = 2.0
    delta = 1e-5

    dp = DifferentialPrivacyEngine(clip_norm=clip_norm, target_epsilon=epsilon, target_delta=delta)

    # 1. Test Clipping
    oversized_weights = np.array([2.0, 3.0, 4.0])
    clipped = dp.clip_weights(oversized_weights)
    norm = float(np.linalg.norm(clipped))
    assert norm <= clip_norm + 1e-6

    # 2. Test Gaussian Noise Injection
    weights = np.zeros(10)
    privatized, meta = dp.privatize_update(weights, seed=42)
    assert meta["epsilon"] == epsilon
    assert meta["delta"] == delta
    assert meta["clip_norm_c"] == clip_norm
    assert np.any(privatized != 0.0) # Noise added


def test_fedavg_mathematical_aggregation():
    # Node 1 has 100 samples with weights [1.0, 1.0]
    # Node 2 has 300 samples with weights [3.0, 3.0]
    # Total samples = 400
    # Expected weighted average = 0.25 * [1.0, 1.0] + 0.75 * [3.0, 3.0] = [2.5, 2.5]
    updates = [
        {
            "node_id": "node-1",
            "weights": np.array([1.0, 1.0]),
            "sample_count": 100,
            "train_loss": 0.08
        },
        {
            "node_id": "node-2",
            "weights": np.array([3.0, 3.0]),
            "sample_count": 300,
            "train_loss": 0.04
        }
    ]

    res = FedAvgCoordinator.aggregate(updates)
    gw = res["global_weights"]

    assert pytest.approx(gw[0], 0.001) == 2.5
    assert pytest.approx(gw[1], 0.001) == 2.5
    assert pytest.approx(res["global_loss"], 0.001) == 0.05 # 0.25*0.08 + 0.75*0.04
    assert len(res["weights_hash"]) == 64
    assert res["total_samples"] == 400


def test_federated_node_client_training():
    client = FederatedNodeClient(
        node_id="node-delhi",
        city="Delhi-NCR",
        sample_count=1500,
        feature_dim=10,
        dp_clip_norm=1.5,
        dp_epsilon=2.0
    )

    update = client.train_epoch(seed=123)
    assert update["node_id"] == "node-delhi"
    assert update["city"] == "Delhi-NCR"
    assert len(update["weights"]) == 10
    assert update["sample_count"] == 1500
    assert "privacy_metadata" in update
    assert update["privacy_metadata"]["epsilon"] == 2.0


# ==============================================================================
# 2. BRICS Multi-Corridor & Declarative Config Tests
# ==============================================================================

def test_brics_multi_corridor_yaml_declarative_portability():
    config = settings.get_corridors_config()
    corridors = config.get("corridors", [])

    corridor_ids = [c["id"] for c in corridors]
    assert "indo-gangetic-main" in corridor_ids
    assert "delhi-ncr-industrial" in corridor_ids
    assert "sao-paulo-campinas" in corridor_ids
    assert "beijing-tianjin-hebei" in corridor_ids

    # Verify São Paulo corridor (Brazil)
    sp = next(c for c in corridors if c["id"] == "sao-paulo-campinas")
    assert sp["country"] == "Brazil"
    assert sp["aqi_standard"] == "conama_brazil"
    assert len(sp["nodes"]) == 3
    node_cities = [n["city"] for n in sp["nodes"]]
    assert "São Paulo Capital" in node_cities
    assert "Campinas" in node_cities

    # Verify Beijing-Tianjin-Hebei corridor (China)
    bth = next(c for c in corridors if c["id"] == "beijing-tianjin-hebei")
    assert bth["country"] == "China"
    assert bth["aqi_standard"] == "mep_china"


def test_brics_aqi_breakpoints_declarative_schemes():
    bp = settings.get_aqi_breakpoints()
    schemes = bp.get("schemes", {})

    assert "cpcb_india" in schemes
    assert "conama_brazil" in schemes
    assert "mep_china" in schemes

    # Validate Brazil CONAMA breakpoints
    conama = schemes["conama_brazil"]
    assert conama["categories"][0]["name"] == "Boa"
    assert conama["categories"][0]["max_c"] == 25.0

    # Validate China MEP breakpoints
    mep = schemes["mep_china"]
    assert mep["categories"][0]["name"] == "Excellent"
    assert mep["categories"][0]["local_name"] == "优"


# ==============================================================================
# 3. Multi-Tenant Partner API Key & Federated Network API Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_partner_api_key_authentication(async_client: AsyncClient):
    # 1. Invalid API Key
    bad_resp = await async_client.get(
        "/api/v1/auth/me",
        headers={"X-API-KEY": "invalid-partner-key"}
    )
    assert bad_resp.status_code == 401

    # 2. Valid Partner API Key
    good_resp = await async_client.get(
        "/api/v1/auth/me",
        headers={"X-API-KEY": "brics-partner-secret-key-001"}
    )
    assert good_resp.status_code == 200
    user_data = good_resp.json()
    assert user_data["email"] == "partner@brics-climate.org"
    assert user_data["role"] == "partner-api-key"


@pytest.mark.asyncio
async def test_federated_status_api(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/federated/status")
    assert resp.status_code == 200
    data = resp.json()

    assert data["coordinator_status"] == "OPERATIONAL"
    assert "Raw data never leaves the node" in data["privacy_contract"]
    assert data["nodes_count"] >= 3
    assert "latest_round" in data


@pytest.mark.asyncio
async def test_federated_round_execution_api(async_client: AsyncClient):
    # Trigger a real FedAvg round across nodes
    run_resp = await async_client.post("/api/v1/federated/rounds/run")
    assert run_resp.status_code == 201
    run_data = run_resp.json()

    assert "round" in run_data
    r = run_data["round"]
    assert r["round_number"] >= 1
    assert len(r["participating_nodes"]) >= 3
    assert r["global_loss"] > 0
    assert r["status"] == "COMPLETED"

    # Query completed rounds list
    list_resp = await async_client.get("/api/v1/federated/rounds")
    assert list_resp.status_code == 200
    rounds = list_resp.json()
    assert len(rounds) >= 1
