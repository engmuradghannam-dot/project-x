"""
🖥️ GPU Integration Module for Project X
Connects the experiment framework to the Virtual GPU Cluster
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .virtual_gpu import VirtualGPUCluster, ExperimentScheduler, ExperimentTask
from .gpu_adapters import GPUProviderFactory, BaseGPUAdapter
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for running an experiment."""
    name: str
    code: str
    estimated_hours: float
    vram_required_gb: int = 16
    priority: int = 1
    preferred_providers: Optional[List[str]] = None


class GPUExperimentRunner:
    """
    🔥 GPU Experiment Runner

    The main interface for running experiments on the Virtual GPU Cluster.
    Automatically handles provider selection, code deployment, and result collection.
    """

    def __init__(self):
        self.cluster = VirtualGPUCluster()
        self.scheduler = ExperimentScheduler(self.cluster)
        self.factory = GPUProviderFactory()
        logger.info("GPU Experiment Runner initialized")

    def run_experiment(self, config: ExperimentConfig) -> Dict[str, Any]:
        """Run a single experiment on the best available GPU."""

        logger.info(f"Submitting experiment: {config.name}")

        # Submit to scheduler
        task_id = self.scheduler.submit_experiment(
            name=config.name,
            estimated_hours=config.estimated_hours,
            vram_required_gb=config.vram_required_gb,
            priority=config.priority,
        )

        # Find the task
        task = next(
            (t for t in self.scheduler.task_queue if t.task_id == task_id),
            None
        )

        if not task:
            return {"error": "Failed to create task"}

        # Schedule it
        self.scheduler.run_scheduler()

        if task.status != "scheduled":
            return {"error": "No GPU available", "task": task_id}

        # Get adapter for the assigned provider
        provider_name = task.assigned_provider.value
        adapter = self.factory.get_adapter(provider_name)

        # Connect and run
        connection = adapter.connect()
        logger.info(f"Connected to {connection.provider_name} ({connection.gpu_type})")

        # Upload and run
        experiment_id = adapter.upload_experiment(config.code)
        result = adapter.run_experiment(experiment_id)

        return {
            "task_id": task_id,
            "experiment_id": experiment_id,
            "provider": provider_name,
            "gpu": connection.gpu_type,
            "vram": connection.vram_gb,
            "status": result.get("status"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def run_batch(self, configs: List[ExperimentConfig]) -> List[Dict[str, Any]]:
        """Run multiple experiments in batch."""
        results = []
        for config in configs:
            result = self.run_experiment(config)
            results.append(result)
        return results

    def get_cluster_status(self) -> Dict[str, Any]:
        """Get current cluster status."""
        return self.cluster.get_cluster_stats()

    def list_providers(self) -> Dict[str, str]:
        """List all available GPU providers."""
        return self.factory.list_providers()


# Convenience function
def run_on_gpu(
    name: str,
    code: str,
    estimated_hours: float = 2,
    vram_gb: int = 16,
    priority: int = 1,
) -> Dict[str, Any]:
    """Quick function to run an experiment on GPU."""
    runner = GPUExperimentRunner()
    config = ExperimentConfig(
        name=name,
        code=code,
        estimated_hours=estimated_hours,
        vram_required_gb=vram_gb,
        priority=priority,
    )
    return runner.run_experiment(config)


# Example usage for Bitcoin experiments
def create_bitcoin_experiment(sample_size: int = 10000) -> ExperimentConfig:
    """Create a Bitcoin key analysis experiment config."""

    code = f'''
import numpy as np
from sklearn.neighbors import NearestNeighbors

# Generate sample keys
keys = np.random.randint(0, 2**256, size={sample_size})

# Extract features (simplified)
def extract_features(keys):
    features = []
    for k in keys:
        b = k.to_bytes(32, 'big')
        features.append([
            np.mean(list(b)),
            np.std(list(b)),
            max(b) - min(b),
        ])
    return np.array(features)

features = extract_features(keys)

# Compute locality
nn = NearestNeighbors(n_neighbors=5)
nn.fit(features)
distances, indices = nn.kneighbors(features)

print(f"Mean distance: {{np.mean(distances):.4f}}")
print(f"Experiment complete!")
'''

    return ExperimentConfig(
        name=f"bitcoin_analysis_{sample_size}",
        code=code,
        estimated_hours=1 if sample_size < 50000 else 4,
        vram_required_gb=16,
        priority=10,
    )
