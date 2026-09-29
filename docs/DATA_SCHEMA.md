# VAYU-NET Data Schema Specification
**Version 1.0 (Digital Public Good Standard)**  
*Corridor: Indo-Gangetic Economic Corridor (Punjab-Haryana-Delhi-UP)*

---

## 1. Ground Monitoring Stations (`stations`)
Physical or reference monitoring stations located across the economic corridor.

| Column | Type | Nullable | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID (String 36) | NO | PK | System-generated station identifier |
| `external_id` | String(100) | NO | UNIQUE | ID from OpenAQ, CPCB, or local municipal authority |
| `name` | String(255) | NO | NO | Human-readable station name (e.g. "Anand Vihar, Delhi") |
| `city` | String(100) | NO | YES | Municipal jurisdiction |
| `state` | String(100) | NO | YES | Administrative state (Punjab, Haryana, Delhi, UP) |
| `latitude` | Float (WGS84) | NO | SPATIAL | Geographic latitude [25.5°N - 32.0°N] |
| `longitude` | Float (WGS84) | NO | SPATIAL | Geographic longitude [73.0°E - 82.0°E] |
| `elevation_m` | Float | YES | NO | Elevation above sea level in meters |
| `is_active` | Boolean | NO | YES | Operational status |
| `data_source` | String(50) | NO | NO | `OPENAQ`, `CPCB`, `OPENMETEO_FALLBACK` |
| `is_stale` | Boolean | NO | NO | Flagged if zero variance across 6h or latency > 2h |
| `last_sync` | Timestamp UTC | YES | NO | Timestamp of latest successful telemetry pull |

---

## 2. Station Measurement Readings (`station_readings`)
Normalized time-series observations from air quality monitors.

| Column | Type | Nullable | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID (String 36) | NO | PK | Reading identifier |
| `station_id` | UUID | NO | FK | Reference to `stations.id` |
| `timestamp` | Timestamp UTC | NO | YES | Observation timestamp in UTC |
| `parameter` | String(20) | NO | YES | `pm25`, `pm10`, `no2`, `so2`, `o3`, `co` |
| `value` | Float | NO | NO | Numerical concentration value |
| `unit` | String(20) | NO | NO | Standard unit (e.g. `ug/m3`, `ppm`) |
| `aqi_value` | Integer | YES | NO | Calculated CPCB NAQI integer (0 - 500) |
| `aqi_category` | String(50) | YES | NO | `Good`, `Satisfactory`, `Moderate`, `Poor`, `Very Poor`, `Severe` |
| `data_origin` | String(20) | NO | YES | `MEASURED` (sensor) or `MODELLED` (atmospheric math) |

---

## 3. Active Fire Detections (`fire_events`)
Satellite active fire radiometry derived from NASA FIRMS VIIRS (375m).

| Column | Type | Nullable | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID (String 36) | NO | PK | Event identifier |
| `external_id` | String(100) | YES | UNIQUE | Natural composite key `viirs_{lat}_{lon}_{time}` |
| `latitude` | Float (WGS84) | NO | SPATIAL | Fire pixel centroid latitude |
| `longitude` | Float (WGS84) | NO | SPATIAL | Fire pixel centroid longitude |
| `brightness_temp_k`| Float | YES | NO | VIIRS I-4 channel brightness temperature (Kelvin) |
| `frp_mw` | Float | NO | NO | Fire Radiative Power in MegaWatts (MW) |
| `acquisition_time` | Timestamp UTC | NO | YES | Satellite overpass timestamp |
| `confidence` | String(20) | YES | NO | Detection confidence (`nominal`, `low`, `high`) |
| `satellite` | String(50) | NO | NO | `VIIRS_SNPP` or `VIIRS_NOAA20` |
| `day_night` | String(5) | YES | NO | `D` (Daytime) or `N` (Nighttime) overpass |

---

## 4. Spatio-Temporal Hotspots (`hotspots`)
DBSCAN clustered high-pollution zones fusing station anomalies, active fires, and reports.

| Column | Type | Nullable | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID (String 36) | NO | PK | Hotspot identifier |
| `corridor_id` | String(100) | YES | YES | Corridor membership |
| `centroid_lat` | Float | NO | SPATIAL | Cluster centroid latitude |
| `centroid_lon` | Float | NO | SPATIAL | Cluster centroid longitude |
| `radius_km` | Float | NO | NO | Spatial extent radius (km) |
| `cluster_size` | Integer | NO | NO | Count of contributing telemetry points |
| `mean_pm25` | Float | YES | NO | Mean PM2.5 within cluster |
| `max_frp_mw` | Float | NO | NO | Maximum fire radiative power observed |
| `probable_source` | String(100) | NO | NO | `Agricultural burning`, `Industrial`, `Traffic-Dust`, `Trans-boundary` |
| `reasoning` | String(500) | NO | NO | Plain-language physical explanation |
| `evidence` | JSON | NO | NO | Attached metrics (bearing, wind speed, fire count, BLH) |
| `severity` | String(50) | NO | NO | `MODERATE`, `HIGH`, `SEVERE`, `CRITICAL` |
| `detected_at` | Timestamp UTC | NO | YES | Timestamp of DBSCAN cluster formation |
| `is_active` | Boolean | NO | YES | Active within current 6-hour evaluation cycle |

---

## 5. Citizen Reports (`citizen_reports`)
Crowdsourced observations with privacy-by-design coordinate rounding and AI validation.

| Column | Type | Nullable | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID (String 36) | NO | PK | Internal report identifier |
| `public_id` | String(20) | NO | UNIQUE | Public tracking ID (e.g. `CR-2026-8921`) |
| `raw_lat` | Float | NO | RESTRICTED | Precise GPS latitude (Admin/Authority only) |
| `raw_lon` | Float | NO | RESTRICTED | Precise GPS longitude (Admin/Authority only) |
| `public_lat` | Float | NO | SPATIAL | Anonymized latitude rounded to 500m grid |
| `public_lon` | Float | NO | SPATIAL | Anonymized longitude rounded to 500m grid |
| `photo_s3_key` | String(255) | YES | NO | MinIO S3 object storage key (EXIF stripped) |
| `user_category` | String(50) | NO | NO | `smoke`, `open_burning`, `dust`, `industrial`, `other` |
| `user_pm25` | Float | YES | NO | Optional low-cost sensor reading (µg/m³) |
| `gemini_classification`| String(50) | YES | NO | Google Gemini Vision classification tag |
| `gemini_confidence`| Float | YES | NO | Model confidence (0.0 to 1.0) |
| `gemini_rationale` | String(500) | YES | NO | Plain-language AI visual reasoning |
| `is_satellite_verified`| Boolean | NO | NO | Verified by nearby active FIRMS VIIRS fire detection |
| `trust_score` | Float | NO | NO | Dynamic score based on sensor & satellite concurrence |
| `status` | String(30) | NO | YES | `PENDING`, `VERIFIED`, `REJECTED` |

---

## 6. Emergency Alerts (`alerts`)
OASIS Common Alerting Protocol (CAP 1.2) compliant emergency directives.

| Column | Type | Nullable | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID (String 36) | NO | PK | Internal alert ID |
| `cap_identifier` | String(100) | NO | UNIQUE | OASIS CAP 1.2 unique URN |
| `corridor_id` | String(100) | YES | YES | Economic corridor identifier |
| `city` | String(100) | NO | YES | Target municipal jurisdiction |
| `severity` | String(30) | NO | YES | `MODERATE`, `HIGH`, `SEVERE`, `EMERGENCY` |
| `title_en` | String(255) | NO | NO | Headline in English |
| `title_hi` | String(255) | NO | NO | Headline in Hindi |
| `description_en`| String(1000) | NO | NO | Public health advisory in English |
| `description_hi`| String(1000) | NO | NO | Public health advisory in Hindi |
| `evidence` | JSON | NO | NO | Underlying physical triggers and sensor thresholds |
| `rule_trigger` | String(100) | NO | NO | `FORECAST_SPIKE`, `UPWIND_FIRE_CLUSTER`, etc. |
| `status` | String(30) | NO | YES | `NEW`, `ACKNOWLEDGED`, `RESOLVED`, `EXPIRED` |
| `acknowledged_by`| String(36) | YES | NO | Operator user ID |
| `resolved_by` | String(36) | YES | NO | Operator user ID |

---

## 7. Model Registry (`model_registry`)
Audit trail and version tracking for predictive atmospheric models.

| Column | Type | Nullable | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID (String 36) | NO | PK | Model registration identifier |
| `model_name` | String(100) | NO | NO | e.g. `xgboost-city-delhi-pm25` |
| `version` | String(50) | NO | NO | Semantic version (e.g. `v1.4.0`) |
| `city` | String(100) | YES | NO | City scope (or `global` for federated network) |
| `metrics` | JSON | NO | NO | Evaluation metrics (`mae`, `rmse`, `baseline_mae`, `r2`) |
| `data_hash` | String(64) | NO | NO | SHA-256 fingerprint of training data window |
| `status` | String(30) | NO | NO | `ACTIVE`, `STAGED`, `ARCHIVED` |

---

## 8. Federated Learning Rounds (`federated_rounds`)
Cryptographic and parameter exchange ledger for cross-municipal / international FedAvg rounds.

| Column | Type | Nullable | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID (String 36) | NO | PK | Round identifier |
| `round_number` | Integer | NO | UNIQUE | Sequential round counter |
| `coordinator_version` | String(50) | NO | NO | Coordinator software/algorithm release tag |
| `participating_nodes` | JSON | NO | NO | Array of participating node IDs |
| `global_loss` | Float | NO | NO | Post-aggregation global loss metric |
| `weight_divergence` | Float | NO | NO | Maximum Euclidean weight distance from prior global model |
| `weights_s3_key` | String(255) | YES | NO | Storage key for aggregated model state dict |
| `status` | String(30) | NO | NO | `IN_PROGRESS`, `COMPLETED`, `REJECTED` |
| `completed_at` | Timestamp UTC | NO | NO | Round completion timestamp |

