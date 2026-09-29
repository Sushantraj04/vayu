#!/usr/bin/env python3
"""
VAYU-NET BRICS Digital Public Good (DPG) Exporter
Exports a localized, turn-key deployment bundle for BRICS partner nations
with zero code modifications required.
"""

import sys
import argparse
import shutil
from pathlib import Path
import yaml


def export_brics_bundle(country: str, corridor_id: str, output_dir: str):
    root_dir = Path(__file__).resolve().parent.parent
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"[*] Packaging VAYU-NET Digital Public Good bundle for {country} ({corridor_id})...")

    # 1. Load and filter corridors.yaml
    corridors_file = root_dir / "backend" / "config" / "corridors.yaml"
    with open(corridors_file, "r", encoding="utf-8") as f:
        all_corridors = yaml.safe_load(f)

    target_corridor = next(
        (c for c in all_corridors.get("corridors", []) if c["id"] == corridor_id),
        None
    )
    if not target_corridor:
        print(f"[!] Warning: Corridor '{corridor_id}' not found in default catalog. Using full catalog.")
        selected_corridors = all_corridors
    else:
        selected_corridors = {
            "version": "1.0",
            "corridors": [target_corridor]
        }

    # 2. Load and filter AQI breakpoints
    breakpoints_file = root_dir / "backend" / "config" / "aqi_breakpoints.yaml"
    with open(breakpoints_file, "r", encoding="utf-8") as f:
        all_bp = yaml.safe_load(f)

    target_scheme = target_corridor.get("aqi_standard", "cpcb_india") if target_corridor else "cpcb_india"
    selected_bp = {
        "schemes": {
            target_scheme: all_bp.get("schemes", {}).get(target_scheme, all_bp.get("schemes", {}).get("cpcb_india"))
        }
    }

    # 3. Create target directory structure
    (out_path / "backend" / "config").mkdir(parents=True, exist_ok=True)
    with open(out_path / "backend" / "config" / "corridors.yaml", "w", encoding="utf-8") as f:
        yaml.dump(selected_corridors, f, sort_keys=False)

    with open(out_path / "backend" / "config" / "aqi_breakpoints.yaml", "w", encoding="utf-8") as f:
        yaml.dump(selected_bp, f, sort_keys=False)

    # 4. Copy backend and frontend source files
    shutil.copytree(root_dir / "backend" / "app", out_path / "backend" / "app", dirs_exist_ok=True)
    shutil.copy(root_dir / "backend" / "requirements.txt", out_path / "backend" / "requirements.txt")
    shutil.copy(root_dir / "backend" / "Dockerfile", out_path / "backend" / "Dockerfile")
    shutil.copy(root_dir / "docker-compose.edge.yml", out_path / "docker-compose.yml")
    shutil.copy(root_dir / ".env.example", out_path / ".env.example")

    # 5. Write Country-Specific Adoption Readme
    readme_content = f"""# VAYU-NET Digital Public Good ({country} Deployment)

Turn-key air quality and pollution-source intelligence platform for the **{target_corridor.get('name', corridor_id) if target_corridor else corridor_id}**.

## Standards Implemented
- **National Standard**: `{target_scheme}`
- **Data Provenance**: Strictly tags `DATA_ORIGIN: MEASURED` vs `MODELLED`
- **Federated Privacy**: Local Differential Privacy with FedAvg parameter aggregation
- **Emergency Feeds**: OASIS Common Alerting Protocol (CAP v1.2) XML and Atom syndication

## Quick Start (Under 3 Minutes)
```bash
cp .env.example .env
docker compose up -d
```
Access the local node at `http://localhost:8000` (API) and `http://localhost:5173` (Portal).
"""
    with open(out_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"[OK] VAYU-NET DPG bundle successfully generated at: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export VAYU-NET DPG Bundle for BRICS Countries")
    parser.add_argument("--country", default="Brazil", help="Target country name")
    parser.add_argument("--corridor", default="sao-paulo-campinas", help="Target corridor ID")
    parser.add_argument("--out", default="./dist-brics-bundle", help="Output directory path")
    args = parser.parse_args()

    export_brics_bundle(args.country, args.corridor, args.out)
