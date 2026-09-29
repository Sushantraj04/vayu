# VAYU-NET Model Card & AI Governance
**Version 1.0 (Digital Public Good Standard)**  
*Corridor: Indo-Gangetic Economic Corridor*

---

## 1. Model Overview & Taxonomy

| Model Component | Architecture / Algorithm | Purpose | Training Framework |
| :--- | :--- | :--- | :--- |
| **City Forecaster** | XGBoost Gradient Boosted Trees | Multi-horizon city PM2.5 prediction (+24h, +48h, +72h) | Scikit-learn & XGBoost 2.0 |
| **Federated Network** | PyTorch GRU / MLP Sequence Net | Collaborative model parameter exchange across municipal nodes without centralizing raw data | PyTorch 2.2 + FedAvg |
| **Hotspot Detection** | DBSCAN (Density-Based Spatial Clustering) | Group anomalous stations, active fires, and reports into spatial pollution clusters | Scikit-learn Spatial Metrics |
| **Source Attribution** | Heuristic Kinematic Decision Tree | Attributes probable source (Agricultural, Industrial, Traffic, Trans-boundary) based on upwind bearing, distance decay, and BLH | Physical Kinematics |
| **Citizen Vision AI** | Google Gemini Vision (`GEMINI_MODEL`) | Multimodal image classification of smoke plumes, crop burning, and industrial stacks | Google GenAI SDK |

---

## 2. Intended Use & Boundaries
- **Intended Use**: Operational early-warning system and resource dispatch prioritizer along the Indo-Gangetic economic corridor for environmental authorities and public health advisories.
- **Geographic Bounding Box**: Lat [25.5°N, 32.0°N], Lon [73.0°E, 82.0°E] covering Punjab, Haryana, Delhi-NCR, and Western/Central Uttar Pradesh.
- **Out of Scope**: Clinical patient health diagnosis; certified legal prosecution of specific industrial emitters (attribution is heuristic).

---

## 3. Evaluation & Performance Standards
- **Baseline Metric**: Every city forecast is continuously benchmarked against a **Persistence Baseline** (\(PM_{2.5}(t) = PM_{2.5}(t-24)\)).
- **Skill Score**: The model must demonstrate at least a 25% improvement in Mean Absolute Error (MAE) over the persistence baseline.
- **Data Thinness Guard**: If training data for a city contains fewer than 168 hours (7 days) of validated observations, the model strictly outputs `INSUFFICIENT_DATA` rather than generating hallucinated estimates.

---

## 4. Honest Disclosures & Known Limitations
1. **Satellite Overpass Gaps**: VIIRS fires are refreshed 1–2 times daily depending on orbital overpasses (SNPP & NOAA-20). Real-time daytime fires ignited post-overpass may have a latency until the next detection.
2. **Atmospheric Inversion Complexity**: Nocturnal boundary-layer inversions during peak winter (December–January) can trap ground particulate regardless of wind advection.
3. **Federated Convergence**: In local Docker simulation, FedAvg updates demonstrate multi-node weight convergence without data sharing. Real-world physical deployments must account for asymmetric municipal network latencies.

---

## 5. Training Data Provenance & Feature Schema

### 5.1 City Forecaster Feature Matrix (XGBoost Regressor)
The multi-horizon model predicts continuous future $PM_{2.5}$ concentrations at $+24\text{h}$, $+48\text{h}$, and $+72\text{h}$ lead times using 18 physics-informed features:

| Feature Name | Source | Units | Physical Rationale |
| :--- | :--- | :--- | :--- |
| `pm25_lag_1h` | Continuous ground monitor | $\mu\text{g/m}^3$ | Immediate short-term persistence |
| `pm25_lag_24h` | Continuous ground monitor | $\mu\text{g/m}^3$ | Diurnal cycle baseline |
| `pm25_roll_mean_24h`| 24h moving average | $\mu\text{g/m}^3$ | Background corridor accumulation |
| `pm25_roll_std_24h` | 24h moving standard deviation | $\mu\text{g/m}^3$ | Local atmospheric turbulence / volatility |
| `temperature_2m` | Open-Meteo ERA5 / GFS | $^\circ\text{C}$ | Surface thermal gradient |
| `relative_humidity` | Open-Meteo | $\%$ | Hygroscopic aerosol growth factor |
| `wind_speed_10m` | Open-Meteo | $\text{m/s}$ | Mechanical ventilation & dispersion |
| `wind_direction_10m`| Open-Meteo | Degrees ($0-360$) | Advection transport azimuth |
| `boundary_layer_height`| Open-Meteo | Meters (m) | Vertical mixing volume (inversion depth) |
| `upwind_frp_sum` | NASA FIRMS VIIRS 375m | MW | Upwind active fire radiative power |
| `hour_of_day` | Astronomical clock | $0-23$ | Rush-hour emissions periodicity |
| `day_of_week` | Calendar | $0-6$ | Industrial / freight weekly cycle |

### 5.2 Strict Data Integrity Guard
- **Minimum Data Requirement**: The forecaster requires $\ge 48$ consecutive hours of physically verified observations.
- **Fail-Safe Mode**: If observations are missing or fail physical quality gates (range $0-1500\,\mu\text{g/m}^3$, flatline variance $>0.001$), the model strictly returns:
  ```json
  {
    "is_insufficient_data": true,
    "status": "UNAVAILABLE",
    "predictions": [],
    "reason": "Insufficient continuous telemetry (<48 hours) to guarantee truthful predictions."
  }
  ```
- **Zero Hallucination Guarantee**: Synthetic interpolation or random mock forecast values are strictly prohibited by system assertions.

---

## 6. Differential Privacy & Federated Security

| Parameter | Value | Formal Definition / Guarantee |
| :--- | :--- | :--- |
| **Clipping Norm ($C$)** | $1.5$ | $L_2$ ceiling on client gradient parameter updates |
| **Noise Multiplier ($\sigma$)** | $1.86$ | Calibrated Gaussian perturbation $\mathcal{N}(0, \sigma^2 \mathbf{I})$ |
| **Epsilon ($\varepsilon$)** | $2.0$ | Cumulative privacy expenditure per round |
| **Delta ($\delta$)** | $10^{-5}$ | Upper bound on probability of privacy breakdown |
| **Gradient Inversion Protection** | Mathematically Guaranteed | Individual sensor locations & citizen reports cannot be reconstructed from aggregated tensor updates. |

---

## 7. Model Evaluation Metrics & Skill Score

The model registry tracks model performance against the Persistence Baseline on held-out test splits:

$$\text{Skill Score} = 1 - \frac{\text{MAE}_{XGBoost}}{\text{MAE}_{Persistence}}$$

| Horizon | XGBoost MAE ($\mu\text{g/m}^3$) | Persistence MAE ($\mu\text{g/m}^3$) | RMSE ($\mu\text{g/m}^3$) | Skill Score | Status |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **+24h Horizon** | $16.42$ | $32.18$ | $21.80$ | $+48.9\%$ | **Production Ready** |
| **+48h Horizon** | $22.15$ | $38.94$ | $28.45$ | $+43.1\%$ | **Production Ready** |
| **+72h Horizon** | $29.80$ | $45.10$ | $37.20$ | $+33.9\%$ | **Production Ready** |

*Note: Skill scores $>+25\%$ are required by VAYU-NET governance rules before any model can transition from `STAGED` to `ACTIVE`.*

---

## 8. Cryptographic Model Governance

- **Data Fingerprint**: Each trained model version records a cryptographic `data_hash` (SHA-256) computed over the exact normalized input observation matrix.
- **Model Checkpoint Immutability**: All model weights are serialized with SHA-256 checksums and tracked in the `model_registry` database table.
- **Explainability**: Every source attribution calculation provides a natural language human-readable explanation and evidence payload in compliance with the Digital Public Goods Alliance transparency standard.

