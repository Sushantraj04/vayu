# VAYU-NET Deployment & Operational Guide
**Version 1.0 (Digital Public Good Standard)**  
*Corridor: Indo-Gangetic Economic Corridor & BRICS Multi-Tenancy*

---

## 1. Deployment Topologies

VAYU-NET supports two primary deployment topologies designed to meet the computational and sovereignty constraints of adopting governments:

### Topology A: Enterprise Cloud / National Hub
Designed for central environmental ministries, state pollution control boards, and national meteorological centers.
- **Components**: PostgreSQL 16 + PostGIS, Redis 7 (broker/cache), MinIO S3 object storage, FastAPI backend cluster, Celery async worker fleet, FedAvg Coordinator, and React Nginx edge proxy.
- **Minimum Requirements**: 4 vCPU, 8 GB RAM, 50 GB NVMe Storage, Linux / Docker Engine 24+.
- **Orchestration**: `docker-compose.yml` or Kubernetes Helm chart.

### Topology B: Municipal Edge Node (<1GB RAM)
Designed for district municipal corporations, local universities, and edge IoT gateway appliances.
- **Components**: Lightweight FastAPI ASGI container with embedded `sqlite+aiosqlite` storage engine, local volume persistence, and periodic differential privacy parameter sync with the central coordinator.
- **Minimum Requirements**: 1 vCPU, 1 GB RAM, 10 GB Storage (Raspberry Pi 4/5, Intel NUC, or municipal VM).
- **Orchestration**: `docker-compose.edge.yml`.

---

## 2. Environment Configuration

Copy the production environment template:
```bash
cp .env.example .env
```

### Key Production Variables:
```ini
# Core Environment
ENVIRONMENT=production
SECRET_KEY=generate-a-cryptographically-secure-random-64-char-string
DATABASE_URL=postgresql+asyncpg://vayunet_user:secure_password@postgres:5432/vayunet_db
REDIS_URL=redis://redis:6379/0

# Storage & Object Store (MinIO / S3)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=vayunet_minio_admin
MINIO_SECRET_KEY=vayunet_minio_secure_secret
MINIO_BUCKET_NAME=vayunet-media

# Upstream Ingestion Credentials
OPENAQ_API_KEY=your_openaq_api_key_here
FIRMS_MAP_KEY=your_nasa_firms_map_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Federated Learning Node ID
FL_NODE_ID=delhi-ncr-hub
FL_COORDINATOR_URL=http://central-coordinator:8005
```

---

## 3. Step-by-Step Deployment Instructions

### 3.1 Option 1: Full-Stack Enterprise Deployment

1. **Build and launch the container topology**:
   ```bash
   docker compose up -d --build
   ```

2. **Verify container health**:
   ```bash
   docker compose ps
   ```
   Ensure `vayunet_backend`, `vayunet_postgres`, `vayunet_redis`, and `vayunet_frontend` report `(healthy)`.

3. **Execute database migrations and seed baseline corridors**:
   ```bash
   docker exec -it vayunet_backend alembic upgrade head
   docker exec -it vayunet_backend python scripts/seed_data.py
   ```

4. **Verify the installation**:
   ```bash
   python scripts/verify_deployment.py --base-url http://localhost:8000
   ```

---

### 3.2 Option 2: Municipal Edge Deployment (<1GB RAM)

For regional airshed nodes operating under memory or bandwidth constraints:

1. **Launch the lightweight edge stack**:
   ```bash
   docker compose -f docker-compose.edge.yml up -d --build
   ```

2. **Verify edge health probe**:
   ```bash
   curl -f http://localhost:8000/api/v1/health
   ```

3. **Check local database initialization**:
   The edge container automatically initializes SQLite schema upon initial startup in `/app/data/vayunet_edge.db`.

---

## 4. BRICS Digital Public Good (DPG) Adoption

Adopting VAYU-NET for a new sovereign or municipal airshed requires **zero Python or React code modifications**:

### Step 1: Export Adopter Bundle
Generate an autonomous deployment bundle:
```bash
python scripts/brics_export.py \
  --country Brazil \
  --corridor sao-paulo-campinas \
  --out dist/dpg_bundles/brazil
```

### Step 2: Configure National Air Quality Breakpoints
If adopting a distinct regulatory standard (e.g., Brazil CONAMA, China MEP, South Africa SANS), declare breakpoints in `backend/config/aqi_breakpoints.yaml`:
```yaml
schemes:
  conama_brazil:
    name: "Brazil CONAMA Resolution 491/2018"
    pollutant: "pm25"
    unit: "ug/m3"
    breakpoints:
      - { low: 0.0, high: 25.0, aqi_low: 0, aqi_high: 40, category: "Boa" }
      - { low: 25.1, high: 50.0, aqi_low: 41, aqi_high: 80, category: "Moderada" }
      - { low: 50.1, high: 75.0, aqi_low: 81, aqi_high: 120, category: "Ruim" }
      - { low: 75.1, high: 125.0, aqi_low: 121, aqi_high: 200, category: "Muito Ruim" }
      - { low: 125.1, high: 500.0, aqi_low: 201, aqi_high: 500, category: "Péssima" }
```

### Step 3: Register Adopter Corridor
In `backend/config/corridors.yaml`, specify boundary coordinates and monitoring stations.

---

## 5. Automated Verification CLI Reference

Run the comprehensive deployment verification suite:
```bash
python scripts/verify_deployment.py --base-url http://localhost:8000
```

The script evaluates 15 criteria:
1. Health liveness (`/api/v1/health`)
2. Multi-service readiness (`/api/v1/ready`)
3. Corridor catalog & bounding polygons (`/api/v1/corridors`)
4. Active monitoring stations (`/api/v1/stations`)
5. Telemetry stream (`/api/v1/readings/latest`)
6. Active VIIRS satellite fires (`/api/v1/satellite/fires`)
7. Atmospheric wind vectors (`/api/v1/weather/current`)
8. DBSCAN spatio-temporal clusters (`/api/v1/analytics/hotspots`)
9. Kinematic source attribution engine (`/api/v1/analytics/attribution`)
10. Multi-horizon city forecast (`/api/v1/forecasts`)
11. AI model registry governance (`/api/v1/models/registry`)
12. OASIS CAP 1.2 XML emergency feed (`/api/v1/alerts/cap/{id}`)
13. Public Atom 1.0 RSS alert syndication (`/api/v1/alerts/feed.atom`)
14. Federated network node directory (`/api/v1/federated/status`)
15. Privacy-preserving FedAvg round execution (`/api/v1/federated/rounds`)

---

## 6. Disaster Recovery & Telemetry Continuity

### Automated Database Backup
```bash
docker exec -t vayunet_postgres pg_dump -U postgres -d vayunet_db -Fc > /var/backups/vayunet_$(date +%Y%m%d_%H%M%S).dump
```

### Database Restoration
```bash
docker exec -i vayunet_postgres pg_restore -U postgres -d vayunet_db --clean < /var/backups/vayunet_target.dump
```

### Failover & Graceful Degradation
- If external OpenAQ feeds experience network timeouts, the platform automatically activates Open-Meteo atmospheric dispersion data and tags incoming telemetry with `DATA_ORIGIN: MODELLED`.
- If NASA FIRMS satellite passes are delayed, DBSCAN spatial clustering falls back to ground station variance and citizen report density.
