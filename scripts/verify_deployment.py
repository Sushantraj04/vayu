#!/usr/bin/env python3
"""
VAYU-NET Production Deployment Verification Script
Automated end-to-end verification of all microservices, telemetry pipelines,
AI intelligence engines, CAP 1.2 XML feeds, and DPG federated endpoints.
"""

import sys
import time
import json
from typing import Dict, Any, List
import urllib.request
import urllib.error

DEFAULT_BASE_URL = "http://127.0.0.1:8000"


def test_endpoint(url: str, name: str, expected_status: int = 200) -> Dict[str, Any]:
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VAYU-NET-Deployment-Verifier/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            elapsed_ms = (time.time() - start) * 1000
            status_code = resp.status
            body = resp.read().decode("utf-8")
            is_json = False
            parsed_data = None
            try:
                parsed_data = json.loads(body)
                is_json = True
            except Exception:
                pass

            success = status_code == expected_status
            return {
                "name": name,
                "url": url,
                "status_code": status_code,
                "elapsed_ms": round(elapsed_ms, 2),
                "success": success,
                "is_json": is_json,
                "data": parsed_data if is_json else body[:100],
            }
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.time() - start) * 1000
        return {
            "name": name,
            "url": url,
            "status_code": e.code,
            "elapsed_ms": round(elapsed_ms, 2),
            "success": e.code == expected_status,
            "error": str(e)
        }
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        return {
            "name": name,
            "url": url,
            "status_code": 0,
            "elapsed_ms": round(elapsed_ms, 2),
            "success": False,
            "error": str(e)
        }


def run_verification(base_url: str = DEFAULT_BASE_URL):
    print("=" * 80)
    print(f" VAYU-NET PRODUCTION DEPLOYMENT & HEALTH VERIFICATION")
    print(f" Target: {base_url}")
    print("=" * 80)

    tests = [
        # 1. Foundation & Probes
        ("/api/v1/health", "System Liveness Probe (/health)", 200),
        ("/api/v1/ready", "Readiness Probe (/ready)", 200),
        ("/api/v1/metrics", "Prometheus Telemetry (/metrics)", 200),

        # 2. Corridors & Ingestion (Phase 1)
        ("/api/v1/corridors/", "Corridors Registry (/corridors/)", 200),
        ("/api/v1/corridors/indo-gangetic-main/summary", "Corridor Risk Summary", 200),
        ("/api/v1/stations/", "Reference Stations (/stations/)", 200),
        ("/api/v1/fires/?hours=24", "NASA FIRMS VIIRS Active Fires (/fires/)", 200),
        ("/api/v1/sources/status", "Data Sources & Provenance (/sources/status)", 200),

        # 3. Intelligence & Modeling (Phase 2)
        ("/api/v1/hotspots/", "DBSCAN Detected Hotspots (/hotspots/)", 200),
        ("/api/v1/attribution/?city=Delhi-NCR", "Kinematic Source Attribution (/attribution/)", 200),
        ("/api/v1/forecasts/?city=Delhi-NCR", "XGBoost City Forecasts (/forecasts/)", 200),
        ("/api/v1/models/", "Model Performance Registry (/models/)", 200),

        # 4. Alerts & Citizen Reports (Phase 3)
        ("/api/v1/alerts/", "Emergency Alerts (/alerts/)", 200),
        ("/api/v1/alerts/feed.atom", "CAP 1.2 Atom Feed (/alerts/feed.atom)", 200),
        ("/api/v1/reports/", "Citizen Reports Feed (/reports/)", 200),

        # 5. DPG Federated Learning (Phase 4)
        ("/api/v1/federated/status", "Federated Network Status (/federated/status)", 200),
    ]

    results = []
    passed = 0

    for endpoint, name, expected in tests:
        url = f"{base_url}{endpoint}"
        res = test_endpoint(url, name, expected)
        results.append(res)

        status_flag = "[PASS]" if res["success"] else "[FAIL]"
        if res["success"]:
            passed += 1
        ms = f"{res['elapsed_ms']}ms".rjust(9)
        print(f" {status_flag} {ms} | {name:<46} -> HTTP {res['status_code']}")

    print("-" * 80)
    print(f" Summary: {passed}/{len(tests)} endpoints healthy and responding ({round(passed / len(tests) * 100, 1)}%)")
    print("=" * 80)

    if passed < len(tests):
        print("Note: To run a full live test, start uvicorn: uvicorn backend.app.main:app --port 8000")
        return False
    return True


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE_URL
    success = run_verification(url)
    sys.exit(0 if success else 1)
