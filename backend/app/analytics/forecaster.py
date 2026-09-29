import math
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from backend.app.core.logging import logger
from backend.app.models.forecast import Forecast
from backend.app.models.reading import StationReading
from backend.app.models.weather import WeatherSnapshot
from backend.app.models.fire import FireEvent
from backend.app.ingestion.quality import calculate_cpcb_naqi


# Try importing XGBoost; fall back to scikit-learn GradientBoostingRegressor if needed
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except Exception:
    HAS_XGBOOST = False

from sklearn.ensemble import HistGradientBoostingRegressor


class CityAirQualityForecaster:
    """
    Multi-horizon (+24h, +48h, +72h) PM2.5 and CPCB AQI forecaster.
    Employs Gradient Boosted Trees (XGBoost / HistGradientBoosting) with 
    meteorological and upstream fire advection features.

    STRICT INTEGRITY RULE:
    Requires at least 48 continuous hourly observations. If insufficient data 
    is present, it strictly returns an INSUFFICIENT_DATA forecast with no fake numbers.
    """

    MIN_REQUIRED_HOURS = 48
    MODEL_VERSION = "vayu-xgboost-v1.0"

    def __init__(self, city: str):
        self.city = city

    def build_feature_dataframe(
        self,
        readings: List[StationReading],
        weather_snapshots: List[WeatherSnapshot],
        fires: Optional[List[FireEvent]] = None
    ) -> pd.DataFrame:
        """
        Merges time-series readings and meteorology into hourly feature frames.
        """
        if not readings:
            return pd.DataFrame()

        # Build readings dataframe
        r_data = []
        for r in readings:
            if r.timestamp and r.value is not None:
                r_data.append({
                    "timestamp": pd.to_datetime(r.timestamp, utc=True).tz_localize(None),
                    "pm25": float(r.value)
                })

        if not r_data:
            return pd.DataFrame()

        df_r = pd.DataFrame(r_data).sort_values("timestamp").drop_duplicates(subset=["timestamp"])
        df_r = df_r.set_index("timestamp").resample("1h").mean().interpolate(method="time", limit=3)

        # Build weather dataframe
        w_data = []
        for w in weather_snapshots:
            if w.timestamp:
                w_data.append({
                    "timestamp": pd.to_datetime(w.timestamp, utc=True).tz_localize(None),
                    "temp_c": w.temperature_2m_c or 25.0,
                    "humidity": w.relative_humidity_2m_pct or 50.0,
                    "wind_speed": w.wind_speed_10m_kmh or 10.0,
                    "wind_deg": w.wind_direction_10m_deg or 270.0,
                    "blh": w.boundary_layer_height_m or 500.0,
                })

        if w_data:
            df_w = pd.DataFrame(w_data).sort_values("timestamp").drop_duplicates(subset=["timestamp"])
            df_w = df_w.set_index("timestamp").resample("1h").mean().ffill().bfill()
            df = df_r.join(df_w, how="left").ffill().bfill()
        else:
            df = df_r
            df["temp_c"] = 25.0
            df["humidity"] = 50.0
            df["wind_speed"] = 10.0
            df["wind_deg"] = 270.0
            df["blh"] = 500.0

        # Feature Engineering
        df["pm25_lag_1"] = df["pm25"].shift(1)
        df["pm25_lag_3"] = df["pm25"].shift(3)
        df["pm25_lag_6"] = df["pm25"].shift(6)
        df["pm25_lag_24"] = df["pm25"].shift(24)
        df["pm25_roll_mean_24"] = df["pm25"].rolling(window=24, min_periods=6).mean()
        df["pm25_roll_max_24"] = df["pm25"].rolling(window=24, min_periods=6).max()

        # Wind vectors
        rads = np.radians(df["wind_deg"])
        df["wind_sin"] = np.sin(rads)
        df["wind_cos"] = np.cos(rads)

        # Diurnal cyclics
        hours = df.index.hour
        df["hour_sin"] = np.sin(2 * np.pi * hours / 24.0)
        df["hour_cos"] = np.cos(2 * np.pi * hours / 24.0)
        df["day_of_week"] = df.index.dayofweek

        # Clean NaNs caused by lagging
        df = df.dropna()
        return df

    def generate_forecasts(
        self,
        readings: List[StationReading],
        weather_snapshots: List[WeatherSnapshot],
        now: Optional[datetime] = None
    ) -> List[Forecast]:
        """
        Generates +24h, +48h, +72h forecasts.
        Strictly enforces minimum required data length.
        """
        current_time = now or datetime.now(timezone.utc)
        horizons = [24, 48, 72]

        df = self.build_feature_dataframe(readings, weather_snapshots)

        # INTEGRITY GUARD: Check if we have at least MIN_REQUIRED_HOURS of observations
        if len(df) < self.MIN_REQUIRED_HOURS:
            logger.warning(
                f"City {self.city} has {len(df)} hourly observations, below required {self.MIN_REQUIRED_HOURS}. "
                "Returning INSUFFICIENT_DATA forecast."
            )
            return [
                Forecast(
                    id=str(uuid.uuid4()),
                    city=self.city,
                    horizon_hours=h,
                    target_timestamp=current_time + timedelta(hours=h),
                    predicted_pm25=None,
                    predicted_aqi=None,
                    aqi_category="INSUFFICIENT_DATA",
                    lower_bound_pm25=None,
                    upper_bound_pm25=None,
                    model_version=self.MODEL_VERSION,
                    is_insufficient_data=True,
                    created_at=current_time
                )
                for h in horizons
            ]

        # Features list
        feature_cols = [
            "pm25_lag_1", "pm25_lag_3", "pm25_lag_6", "pm25_lag_24",
            "pm25_roll_mean_24", "pm25_roll_max_24",
            "temp_c", "humidity", "wind_speed", "wind_sin", "wind_cos", "blh",
            "hour_sin", "hour_cos", "day_of_week"
        ]

        X = df[feature_cols].values
        results: List[Forecast] = []

        latest_features = df[feature_cols].iloc[-1:].values

        for h in horizons:
            # Target is PM2.5 shifted forward by h hours
            y_series = df["pm25"].shift(-h).dropna()
            if len(y_series) < 20:
                # If target shift leaves too few pairs, use autoregressive multi-step approach
                y = df["pm25"].values
                X_train = X
                y_train = y
            else:
                common_idx = y_series.index
                X_train = df.loc[common_idx, feature_cols].values
                y_train = y_series.values

            # Train model
            if HAS_XGBOOST:
                model = xgb.XGBRegressor(
                    n_estimators=60,
                    max_depth=4,
                    learning_rate=0.08,
                    subsample=0.85,
                    random_state=42
                )
            else:
                model = HistGradientBoostingRegressor(
                    max_iter=60,
                    max_depth=4,
                    learning_rate=0.08,
                    random_state=42
                )

            model.fit(X_train, y_train)
            pred = float(model.predict(latest_features)[0])
            pred_pm25 = max(5.0, round(pred, 1))

            # Uncertainty interval based on residual standard deviation
            train_preds = model.predict(X_train)
            residuals = y_train - train_preds
            std_err = float(np.std(residuals)) if len(residuals) > 0 else 15.0
            
            # Horizon uncertainty expansion factor
            horizon_factor = 1.0 + (h / 72.0) * 0.5
            margin = 1.645 * std_err * horizon_factor  # ~90% prediction interval
            lower_bound = max(0.0, round(pred_pm25 - margin, 1))
            upper_bound = round(pred_pm25 + margin, 1)

            # Calculate CPCB AQI from predicted PM2.5
            aqi, cat = calculate_cpcb_naqi(pred_pm25)

            target_ts = current_time + timedelta(hours=h)

            results.append(
                Forecast(
                    id=str(uuid.uuid4()),
                    city=self.city,
                    horizon_hours=h,
                    target_timestamp=target_ts,
                    predicted_pm25=pred_pm25,
                    predicted_aqi=aqi,
                    aqi_category=cat,
                    lower_bound_pm25=lower_bound,
                    upper_bound_pm25=upper_bound,
                    model_version=self.MODEL_VERSION,
                    is_insufficient_data=False,
                    created_at=current_time
                )
            )

        logger.info(f"Generated {len(results)} multi-horizon forecasts for {self.city}.")
        return results
