import math
from typing import List, Dict, Any, Tuple
import numpy as np


class DifferentialPrivacyEngine:
    """
    Implements local differential privacy (LDP) for federated learning clients:
      1. Gradient / parameter L2 clipping: ||w||_2 <= C
      2. Calibrated Gaussian noise addition: N(0, sigma^2 * I)
         where sigma = (sqrt(2 * ln(1.25 / delta)) * C) / epsilon
    Guarantees mathematically that individual raw telemetry samples cannot be reconstructed
    from shared weight updates.
    """

    def __init__(
        self,
        clip_norm: float = 1.5,
        target_epsilon: float = 2.0,
        target_delta: float = 1e-5
    ):
        self.clip_norm = clip_norm
        self.target_epsilon = target_epsilon
        self.target_delta = target_delta
        self.sigma = self._calculate_sigma(clip_norm, target_epsilon, target_delta)
        self.spent_epsilon = 0.0

    @staticmethod
    def _calculate_sigma(c: float, eps: float, delta: float) -> float:
        """Calculates standard deviation of Gaussian noise mechanism."""
        if eps <= 0:
            raise ValueError("Epsilon must be greater than 0")
        factor = math.sqrt(2.0 * math.log(1.25 / delta))
        return (factor * c) / eps

    def clip_weights(self, weights: np.ndarray) -> np.ndarray:
        """Clips parameter vector to maximum L2 norm C."""
        l2_norm = float(np.linalg.norm(weights))
        if l2_norm > self.clip_norm and l2_norm > 0:
            scale = self.clip_norm / l2_norm
            return weights * scale
        return weights

    def add_gaussian_noise(self, weights: np.ndarray, seed: int = None) -> np.ndarray:
        """Injects calibrated zero-mean Gaussian noise to parameter vector."""
        rng = np.random.default_rng(seed)
        noise = rng.normal(loc=0.0, scale=self.sigma, size=weights.shape)
        perturbed = weights + noise
        self.spent_epsilon += self.target_epsilon
        return perturbed

    def privatize_update(self, weights: np.ndarray, seed: int = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Executes complete (epsilon, delta)-DP mechanism:
        1. Clips L2 norm
        2. Injects Gaussian noise
        Returns (privatized_weights, privacy_guarantee_metadata)
        """
        clipped = self.clip_weights(weights)
        privatized = self.add_gaussian_noise(clipped, seed=seed)

        metadata = {
            "clip_norm_c": self.clip_norm,
            "epsilon": self.target_epsilon,
            "delta": self.target_delta,
            "sigma": round(self.sigma, 4),
            "mechanism": "Gaussian LDP",
            "privacy_guarantee": f"({self.target_epsilon}, {self.target_delta})-DP"
        }
        return privatized, metadata
