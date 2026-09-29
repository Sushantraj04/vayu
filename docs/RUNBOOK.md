# VAYU-NET Operations Runbook
**Version 1.0 (Digital Public Good Standard)**

---

## 1. Routine Operations & Maintenance

### 1.1 Service Health Probes
Verify health and backing service readiness:
```bash
# Liveness probe
curl -f http://localhost:8000/api/v1/health

# Readiness probe (validates DB, Redis, MinIO)
curl -f http://localhost:8000/api/v1/ready
```

### 1.2 Database Backup & PostGIS Snapshot
```bash
# Automated nightly backup of PostgreSQL + PostGIS
docker exec -t vayunet_postgres pg_dump -U postgres -d vayunet_db -Fc > vayunet_backup_$(date +%Y%m%d).dump

# Restore from snapshot
docker exec -i vayunet_postgres pg_restore -U postgres -d vayunet_db --clean < vayunet_backup_20260928.dump
```

---

## 2. Onboarding a New Corridor or City
To introduce a new economic corridor (e.g. for BRICS partner adoption in São Paulo, Johannesburg, or Yangtze River Delta):

1. Open `/backend/config/corridors.yaml`.
2. Append the new corridor specification:
```yaml
  - id: "brazil-sao-paulo-belt"
    name: "São Paulo Industrial & Agricultural Corridor"
    code: "SP_IND"
    bounding_box:
      min_lat: -24.2
      max_lat: -22.5
      min_lon: -47.8
      max_lon: -45.5
    nodes:
      - city: "Campinas"
        state: "São Paulo"
        lat: -22.9099
        lon: -47.0626
        order: 1
      - city: "São Paulo"
        state: "São Paulo"
        lat: -23.5505
        lon: -46.6333
        order: 2
        is_hub: true
```
3. Restart backend or trigger config reload. **Zero Python or React code modifications required.**

---

## 3. Incident Response & Troubleshooting

### 3.1 OpenAQ Station Telemetry Gaps
- **Symptom**: Station telemetry displays `Delayed` or `Stale` badge in Situation Room.
- **Root Cause**: Upstream CPCB/OpenAQ station maintenance or network outage.
- **Action**: VAYU-NET automatically activates Open-Meteo Air Quality atmospheric dispersion as boundary condition and tags telemetry with `DATA_ORIGIN: MODELLED_ESTIMATE`. No manual intervention required.

### 3.2 Celery Worker Queue Backlog
- **Symptom**: Hotspot clustering or alert evaluations delayed.
- **Action**: Check Redis queue depth and scale workers:
```bash
docker exec -it vayunet_redis redis-cli llen celery
docker compose up -d --scale celery_worker=4
```

---

## 4. Emergency Smog Episodes & GRAP Escalation

During acute trans-boundary pollution episodes (e.g. stubble burning season, thermal inversions):

### 4.1 Triggering Immediate Ingestion & Kinematic Attribution
Force an out-of-band ingestion cycle and source attribution run:
```bash
# Execute asynchronous Celery ingestion tasks immediately
docker exec -it vayunet_backend python -c "
from backend.app.tasks.ingestion_tasks import ingest_all_corridors_task
res = ingest_all_corridors_task.delay()
print(f'Triggered task: {res.id}')
"
```

### 4.2 Manual Federated Learning Coordination Round
To execute an emergency FedAvg round across all regional nodes:
```bash
curl -X POST http://localhost:8000/api/v1/federated/rounds \
  -H "Authorization: Bearer <OPERATOR_JWT_TOKEN>" \
  -H "Content-Type: application/json"
```

### 4.3 CAP 1.2 Alert Dispatch & Verification
Inspect the latest generated OASIS CAP 1.2 emergency payload:
```bash
# Fetch active alerts
curl -s http://localhost:8000/api/v1/alerts | jq .

# Fetch machine-readable CAP XML for Alert #1
curl -s http://localhost:8000/api/v1/alerts/cap/<ALERT_ID> -H "Accept: application/xml"
```

### 4.4 Citizen Report Moderation & Triage
Authorized municipal personnel can audit crowdsourced incident submissions:
```bash
# Retrieve pending citizen reports
curl -s http://localhost:8000/api/v1/reports \
  -H "Authorization: Bearer <AUTHORITY_JWT_TOKEN>" | jq .
```
Reports with `is_satellite_verified: true` and `trust_score >= 0.8` are automatically elevated into the Situation Room map layer.

