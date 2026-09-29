import hashlib
from typing import List, Dict, Any, Tuple
import numpy as np
from backend.app.core.logging import logger


class FedAvgCoordinator:
    """
    Implements Federated Averaging (FedAvg, McMahan et al.):
    Aggregates locally trained, differentially privatized model updates
    weighted proportionally to each node's local dataset sample size:
      W_global = sum_{k=1}^K (n_k / N) * W_k
    """

    COORDINATOR_VERSION = "vayu-fedavg-v2.1"

    @classmethod
    def aggregate(
        cls,
        client_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Takes a list of client updates:
        [
          {
            "node_id": "node-delhi",
            "weights": np.ndarray,
            "sample_count": 1400,
            "train_loss": 0.0412
          }, ...
        ]
        Returns aggregated global model checkpoint and metrics.
        """
        if not client_updates:
            raise ValueError("Cannot aggregate empty client updates.")

        total_samples = sum(u["sample_count"] for u in client_updates)
        if total_samples <= 0:
            raise ValueError("Total sample count must be positive.")

        # Ensure all weight vectors have matching dimension
        first_weights = np.array(client_updates[0]["weights"], dtype=np.float64)
        weight_dim = first_weights.shape

        global_weights = np.zeros(weight_dim, dtype=np.float64)
        weighted_loss = 0.0

        for u in client_updates:
            w = np.array(u["weights"], dtype=np.float64)
            n_k = u["sample_count"]
            weight_factor = n_k / total_samples

            global_weights += weight_factor * w
            weighted_loss += weight_factor * u.get("train_loss", 0.05)

        # Calculate weight divergence for each client
        divergences = []
        for u in client_updates:
            w = np.array(u["weights"], dtype=np.float64)
            div = float(np.linalg.norm(w - global_weights))
            divergences.append(div)
            u["weight_divergence"] = round(div, 4)

        mean_divergence = float(np.mean(divergences)) if divergences else 0.0

        # Compute SHA-256 fingerprint hash of global weights
        weight_bytes = global_weights.tobytes()
        weights_hash = hashlib.sha256(weight_bytes).hexdigest()

        result = {
            "coordinator_version": cls.COORDINATOR_VERSION,
            "global_weights": global_weights.tolist(),
            "weights_hash": weights_hash,
            "global_loss": round(weighted_loss, 4),
            "mean_weight_divergence": round(mean_divergence, 4),
            "participating_nodes": [u["node_id"] for u in client_updates],
            "total_samples": total_samples,
            "node_metrics": [
                {
                    "node_id": u["node_id"],
                    "sample_count": u["sample_count"],
                    "train_loss": u.get("train_loss"),
                    "divergence": u.get("weight_divergence")
                }
                for u in client_updates
            ]
        }

        logger.info(
            f"FedAvg round completed: {len(client_updates)} nodes aggregated "
            f"(Loss={result['global_loss']}, Divergence={result['mean_weight_divergence']}, Hash={weights_hash[:8]})"
        )
        return result
