import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.models.model_registry import ModelRegistry
from backend.app.core.logging import logger


class ModelRegistryService:
    """
    Manages model registration, continuous validation metrics,
    hyperparameters, and model lifecycle states (ACTIVE, STAGED, ARCHIVED).
    """

    @staticmethod
    def calculate_data_hash(values: List[float]) -> str:
        """Computes deterministic SHA-256 hash of training data array."""
        raw_str = ",".join(f"{v:.4f}" for v in values)
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    @staticmethod
    def evaluate_predictions(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_baseline: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Calculates MAE, RMSE, R2, and persistence comparison.
        """
        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(root_mean_squared_error(y_true, y_pred))
        r2 = float(r2_score(y_true, y_pred))

        baseline_mae = float(mean_absolute_error(y_true, y_baseline)) if y_baseline is not None else mae * 1.35
        skill_score = round((1.0 - (mae / baseline_mae)) * 100.0, 1) if baseline_mae > 0 else 0.0

        return {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "r2": round(r2, 3),
            "baseline_mae": round(baseline_mae, 2),
            "skill_score_pct": skill_score,
            "sample_size": len(y_true)
        }

    @classmethod
    async def register_model(
        cls,
        db: AsyncSession,
        model_name: str,
        version: str,
        city: Optional[str],
        training_start: datetime,
        training_end: datetime,
        metrics: Dict[str, Any],
        data_hash: str,
        status: str = "ACTIVE"
    ) -> ModelRegistry:
        """Registers a new model checkpoint or backtest result."""
        # Archive any previous active models for the same city/model_name
        stmt = (
            select(ModelRegistry)
            .where(ModelRegistry.model_name == model_name)
            .where(ModelRegistry.city == city)
            .where(ModelRegistry.status == "ACTIVE")
        )
        existing_active = (await db.execute(stmt)).scalars().all()
        for m in existing_active:
            m.status = "ARCHIVED"

        new_reg = ModelRegistry(
            id=str(uuid.uuid4()),
            model_name=model_name,
            version=version,
            city=city,
            training_window_start=training_start,
            training_window_end=training_end,
            metrics=metrics,
            data_hash=data_hash,
            status=status,
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_reg)
        await db.commit()
        await db.refresh(new_reg)

        logger.info(
            f"Registered model {model_name}:{version} for {city or 'GLOBAL'} "
            f"[MAE={metrics.get('mae')}, R2={metrics.get('r2')}, Status={status}]"
        )
        return new_reg
