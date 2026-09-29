# VAYU-NET Security & Privacy Architecture
**Version 1.0 (Digital Public Good Standard)**

---

## 1. Threat Model & Mitigations

| Threat Vector | Attack Scenario | Architectural Mitigation |
| :--- | :--- | :--- |
| **Citizen Photo Exploitation** | Malicious file uploads (executable payload, steganography, oversized images). | Strict MIME-type gating (JPEG/PNG only), 10MB file size ceiling, PIL stream reprocessing, and complete EXIF header sanitization before persisting to MinIO S3. |
| **Citizen Geolocation Deanonymization** | Tracking individual citizen residences from reported incident coordinates. | The exact coordinate `(raw_lat, raw_lon)` is restricted to encrypted administrative tables. All public map layers and API responses round coordinates to a **500m spatial grid** (\(\approx 0.005^\circ\)). Zero PII collected. |
| **Alert Fatigue & DoS** | Flooding alert channels with duplicate warnings during continuous high-AQI events. | Automated 4-hour spatial cooldown deduplication per corridor grid cell. Alert lifecycle enforces state transition (`NEW` → `ACKNOWLEDGED` → `RESOLVED`). |
| **Credential & API Key Leaks** | Accidental exposure of `OPENAQ_API_KEY`, `FIRMS_MAP_KEY`, or `GEMINI_API_KEY`. | Zero secrets committed to source. Environment variables only via `.env` / `.env.example`. Automated git pre-commit hook scanning. |
| **Unauthorized Administrative Action** | Compromise of system settings, role escalations, or emergency directive issuance. | Strict Role-Based Access Control (RBAC) via cryptographically signed JWT tokens (HS256) and immutable append-only audit logging (`audit_logs` table) recording user ID, action, resource, timestamp, and IP. |

---

## 2. RBAC Permissions Matrix

| Endpoint Group | Public | Authority | Analyst | Admin | Partner API |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `GET /api/v1/health`, `/ready` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `GET /api/v1/corridors/**` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `POST /api/v1/reports` (Citizen) | ✓ (Anon) | ✓ | ✓ | ✓ | ✓ |
| `GET /api/v1/reports/queue` | ✗ | ✓ | ✓ | ✓ | ✗ |
| `PUT /api/v1/alerts/{id}/ack` | ✗ | ✓ | ✗ | ✓ | ✗ |
| `PUT /api/v1/alerts/{id}/resolve` | ✗ | ✓ | ✗ | ✓ | ✗ |
| `GET /api/v1/models/performance` | ✗ | ✓ | ✓ | ✓ | ✓ |
| `POST /api/v1/users/**` | ✗ | ✗ | ✗ | ✓ | ✗ |
| `GET /api/v1/audit/**` | ✗ | ✓ | ✓ | ✓ | ✗ |
| `GET /api/v1/metrics` (Prometheus) | ✗ | ✗ | ✗ | ✓ | ✓ |

---

## 3. Reverse Proxy & Network Hardening
The Nginx edge proxy applies standard OWASP security headers:
```nginx
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```
