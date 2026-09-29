from typing import Dict, Any, List, Optional
import numpy as np

from backend.app.federated.privacy import DifferentialPrivacyEngine


class FederatedNodeClient:
    """
    Simulates / represents a federated learning client node at a municipal airshed.
    Enforces the core DPG privacy principle:
      "Raw telemetry never leaves the node boundaries."
    Trains local parameters on local data and applies (epsilon, delta)-Differential Privacy
    before transmitting weights to the FedAvg coordinator.
    """

    def __init__(
        self,
        node_id: str,
        city: str,
        sample_count: int = 1000,
        feature_dim: int = 15,
        dp_clip_norm: float = 1.5,
        dp_epsilon: float = 2.0,
        dp_delta: float = 1e-5
    ):
        self.node_id = node_id
        self.city = city
        self.sample_count = sample_count
        self.feature_dim = feature_dim
        self.dp_engine = DifferentialPrivacyEngine(
            clip_norm=dp_clip_norm,
            target_epsilon=dp_epsilon,
            target_delta=dp_delta
        )
        self.local_weights = np.zeros(feature_dim, dtype=np.float64)

    def train_epoch(
        self,
        global_weights: Optional[List[float]] = None,
        learning_rate: float = 0.05,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes local training step initialized from global_weights (if provided),
        computes local model gradient, and returns differentially privatized weights.
        """
        rng = np.random.default_rng(seed)

        if global_weights is not None:
            self.local_weights = np.array(global_weights, dtype=np.float64)
        else:
            self.local_weights = rng.normal(loc=0.0, scale=0.1, size=self.feature_dim)

        # Simulate synthetic local gradient based on node's regional air quality variance
        # In production this executes local PyTorch / Scikit optimizer step
        local_gradient = rng.normal(loc=-0.02, scale=0.15, size=self.feature_dim)
        updated_weights = self.local_weights - learning_rate * local_gradient

        # Apply Differential Privacy (clipping + Gaussian noise)
        privatized_weights, dp_meta = self.dp_engine.privatize_update(updated_weights, seed=seed)
        self.local_weights = privatized_weights

        train_loss = float(max(0.01, 0.08 + rng.normal(0.0, 0.01)))

        return {
            "node_id": self.node_id,
            "city": self.city,
            "weights": privatized_weights.tolist(),
            "sample_count": self.sample_count,
            "train_loss": round(train_loss, 4),
            "privacy_metadata": dp_meta
        }
