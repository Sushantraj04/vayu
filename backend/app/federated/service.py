import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.models.federated import FederatedRound
from backend.app.federated.aggregator import FedAvgCoordinator
from backend.app.federated.client import FederatedNodeClient
from backend.app.core.logging import logger


class FederatedLearningService:
    """
    Orchestrates federated learning rounds, client training,
    FedAvg aggregation, and database persistence.
    """

    DEFAULT_NODES = [
        {"node_id": "node-ludhiana", "city": "Ludhiana", "samples": 1200},
        {"node_id": "node-delhi", "city": "Delhi-NCR", "samples": 2800},
        {"node_id": "node-lucknow", "city": "Lucknow", "samples": 1500},
        {"node_id": "node-sao-paulo", "city": "São Paulo", "samples": 2200}
    ]

    @classmethod
    async def run_federated_round(
        cls,
        db: AsyncSession,
        nodes: Optional[List[Dict[str, Any]]] = None,
        feature_dim: int = 15
    ) -> FederatedRound:
        """
        Executes a complete federated training round across nodes:
        1. Queries latest round number
        2. Dispatches local training step with Differential Privacy on each node
        3. Coordinates FedAvg parameter aggregation
        4. Persists the round results to the database
        """
        active_nodes = nodes or cls.DEFAULT_NODES

        # 1. Determine next round number
        stmt = select(FederatedRound).order_by(desc(FederatedRound.round_number)).limit(1)
        last_round = (await db.execute(stmt)).scalar_one_or_none()
        next_round_num = (last_round.round_number + 1) if last_round else 1

        # 2. Local client training with Differential Privacy
        client_updates = []
        for n in active_nodes:
            client = FederatedNodeClient(
                node_id=n["node_id"],
                city=n["city"],
                sample_count=n.get("samples", 1000),
                feature_dim=feature_dim
            )
            update = client.train_epoch()
            client_updates.append(update)

        # 3. FedAvg Aggregation
        aggregated = FedAvgCoordinator.aggregate(client_updates)

        # 4. Save FederatedRound to DB
        round_record = FederatedRound(
            id=str(uuid.uuid4()),
            round_number=next_round_num,
            coordinator_version=aggregated["coordinator_version"],
            participating_nodes=aggregated["participating_nodes"],
            global_loss=aggregated["global_loss"],
            weight_divergence=aggregated["mean_weight_divergence"],
            weights_s3_key=f"weights/global-round-{next_round_num}-{aggregated['weights_hash'][:8]}.pt",
            status="COMPLETED",
            completed_at=datetime.now(timezone.utc)
        )

        db.add(round_record)
        await db.commit()
        await db.refresh(round_record)

        logger.info(
            f"Successfully executed and recorded FederatedRound #{round_record.round_number} "
            f"(Loss: {round_record.global_loss:.4f}, Nodes: {len(round_record.participating_nodes)})"
        )
        return round_record
