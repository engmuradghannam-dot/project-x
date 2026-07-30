\"\"\"
ParallelExperimentRunner - Runs experiments across 100 GPU nodes
\"\"\"

import time
import numpy as np
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass

from .cluster_manager import GPUCluster, ClusterConfig
from .cluster_node import ClusterNode


@dataclass
class ExperimentBatch:
    \"\"\"A batch of experiments to run.\"\"\"
    batch_id: str
    experiments: List[Dict[str, Any]]
    description: str = ""


def bitcoin_experiment_worker(gpu, sample_size: int = 10000, seed: int = 42, **kwargs) -> Dict[str, Any]:
    \"\"\"
    Bitcoin key analysis experiment worker.
    Runs on a single GPU node.
    \"\"\"
    np.random.seed(seed)

    # Allocate on GPU
    keys = gpu.allocate((sample_size,), dtype=np.uint64)
    keys[:] = np.random.randint(0, 2**64, size=sample_size, dtype=np.uint64)

    # Extract features
    features = np.zeros((sample_size, 24), dtype=np.float32)
    for i in range(sample_size):
        k = keys[i]
        bytes_arr = np.array([(k >> (8*j)) & 0xFF for j in range(8)], dtype=np.float32)
        features[i, 0] = np.mean(bytes_arr)
        features[i, 1] = np.std(bytes_arr)
        features[i, 2] = np.min(bytes_arr)
        features[i, 3] = np.max(bytes_arr)
        features[i, 4] = np.sum(bytes_arr > 127)

    # Compute statistics
    mean_feat = np.mean(features[:, 0])
    std_feat = np.std(features[:, 0])

    # Compute pairwise distances (sample)
    n_pairs = min(1000, sample_size)
    distances = []
    for i in range(n_pairs):
        j = np.random.randint(0, sample_size)
        dist = np.linalg.norm(features[i] - features[j])
        distances.append(dist)

    # Free memory
    gpu.free(keys)

    return {
        "sample_size": sample_size,
        "seed": seed,
        "mean_feature": float(mean_feat),
        "std_feature": float(std_feat),
        "mean_distance": float(np.mean(distances)),
        "std_distance": float(np.std(distances)),
    }


def muradengine_test7_worker(gpu, node_id: str, batch_start: int, batch_size: int, **kwargs) -> Dict[str, Any]:
    \"\"\"
    MuradEngine Test 7: Scaling Test Worker
    Each node processes a batch of keys for large-scale analysis.
    \"\"\"
    import hashlib

    results = []

    for i in range(batch_size):
        # Generate key from batch
        key_seed = batch_start + i
        key_bytes = hashlib.sha256(str(key_seed).encode()).digest()
        key_int = int.from_bytes(key_bytes, 'big')

        # Extract features (simplified for speed)
        features = {
            "msb": (key_int >> 248) & 0xFF,
            "lsb": key_int & 0xFF,
            "popcount": bin(key_int).count('1'),
            "byte_sum": sum((key_int >> (8*j)) & 0xFF for j in range(32)),
        }

        results.append(features)

    # Aggregate
    msb_values = [r["msb"] for r in results]
    popcounts = [r["popcount"] for r in results]

    return {
        "node_id": node_id,
        "batch_start": batch_start,
        "batch_size": batch_size,
        "msb_mean": float(np.mean(msb_values)),
        "msb_std": float(np.std(msb_values)),
        "popcount_mean": float(np.mean(popcounts)),
        "popcount_std": float(np.std(popcounts)),
    }


class ParallelExperimentRunner:
    \"\"\"
    Runs experiments in parallel across GPU cluster.
    \"\"\"

    def __init__(self, num_nodes: int = 100):
        self.cluster = GPUCluster(ClusterConfig(num_nodes=num_nodes))
        self.results = []

    def run_bitcoin_batch(self, total_samples: int = 1000000, samples_per_node: int = 10000) -> List[Dict[str, Any]]:
        \"\"\"
        Run Bitcoin analysis across all nodes.

        Example: 1M samples / 100 nodes = 10K samples per node
        \"\"\"
        num_experiments = total_samples // samples_per_node

        experiments = []
        for i in range(num_experiments):
            experiments.append({
                "id": f"btc_batch_{i:04d}",
                "function": bitcoin_experiment_worker,
                "parameters": {
                    "sample_size": samples_per_node,
                    "seed": i * 1000,
                },
            })

        with self.cluster:
            results = self.cluster.run_parallel_experiments(experiments)

        self.results = results
        return results

    def run_muradengine_test7(self, total_keys: int = 100000, keys_per_node: int = 1000) -> List[Dict[str, Any]]:
        \"\"\"
        Run MuradEngine Test 7 (Scaling) across cluster.

        Test 7 needs: 100K+ training, 20K+ test
        With 100 nodes: 1K keys per node = 100K total
        \"\"\"
        num_batches = total_keys // keys_per_node

        experiments = []
        for i in range(num_batches):
            experiments.append({
                "id": f"test7_batch_{i:04d}",
                "function": muradengine_test7_worker,
                "parameters": {
                    "node_id": f"node_{i:03d}",
                    "batch_start": i * keys_per_node,
                    "batch_size": keys_per_node,
                },
            })

        with self.cluster:
            results = self.cluster.run_parallel_experiments(experiments)

        self.results = results
        return results

    def aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        \"\"\"Aggregate results from all nodes.\"\"\"
        if not results:
            return {}

        # Collect all numeric metrics
        aggregated = {
            "total_experiments": len(results),
            "successful": sum(1 for r in results if r.get("status") == "success"),
            "failed": sum(1 for r in results if r.get("status") == "failed"),
            "total_compute_time": sum(r.get("duration", 0) for r in results),
        }

        # Aggregate result metrics
        all_result_values = {}
        for r in results:
            if "result" in r and isinstance(r["result"], dict):
                for key, value in r["result"].items():
                    if isinstance(value, (int, float)):
                        if key not in all_result_values:
                            all_result_values[key] = []
                        all_result_values[key].append(value)

        for key, values in all_result_values.items():
            aggregated[f"{key}_mean"] = float(np.mean(values))
            aggregated[f"{key}_std"] = float(np.std(values))
            aggregated[f"{key}_min"] = float(np.min(values))
            aggregated[f"{key}_max"] = float(np.max(values))

        return aggregated

    def generate_report(self, results: List[Dict[str, Any]], test_name: str = "Test") -> str:
        \"\"\"Generate a text report.\"\"\"
        agg = self.aggregate_results(results)

        lines = [
            "=" * 70,
            f"  {test_name} - PARALLEL EXECUTION REPORT",
            "=" * 70,
            "",
            "  Cluster Configuration:",
            f"    Nodes: {self.cluster.config.num_nodes}",
            f"    VRAM/Node: {self.cluster.config.vram_per_node_gb} GB",
            f"    Total VRAM: {self.cluster.config.num_nodes * self.cluster.config.vram_per_node_gb} GB",
            "",
            "  Execution Summary:",
            f"    Total Experiments: {agg.get('total_experiments', 0)}",
            f"    Successful: {agg.get('successful', 0)}",
            f"    Failed: {agg.get('failed', 0)}",
            f"    Total Compute Time: {agg.get('total_compute_time', 0):.2f}s",
            "",
            "  Aggregated Results:",
        ]

        for key in sorted(agg.keys()):
            if key.endswith("_mean"):
                metric = key[:-5]
                mean = agg.get(f"{metric}_mean", 0)
                std = agg.get(f"{metric}_std", 0)
                lines.append(f"    {metric}: {mean:.4f} +/- {std:.4f}")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)
