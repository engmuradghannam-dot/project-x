#!/usr/bin/env python3
"""
GPU Cluster Demo - 100 Parallel Nodes
Demonstrates running experiments across 100 GPU instances
"""

import sys
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.gpu_cluster import GPUCluster
from src.cluster_network import ClusterNetwork
from rich.console import Console

console = Console()


def bitcoin_experiment(node, sample_size=10000, **kwargs):
    """Bitcoin key analysis experiment."""
    keys = np.random.randint(0, 2**64, size=sample_size, dtype=np.uint64)

    features = np.zeros((sample_size, 8), dtype=np.float32)
    for i in range(min(sample_size, 1000)):
        k = keys[i]
        bytes_arr = np.array([(k >> (8*j)) & 0xFF for j in range(8)], dtype=np.float32)
        features[i, 0] = np.mean(bytes_arr)
        features[i, 1] = np.std(bytes_arr)

    return {
        "node_id": node.node_id,
        "node_type": node.gpu_type,
        "sample_size": sample_size,
        "mean_feature": float(np.mean(features[:1000, 0])),
    }


def main():
    print("=" * 70)
    print("PROJECT X - 100 GPU CLUSTER DEMO")
    print("=" * 70)

    cluster = GPUCluster(num_nodes=100)
    network = ClusterNetwork(cluster)
    cluster.print_status()

    tasks = [
        {"name": f"bitcoin_analysis_node_{i}", "params": {"sample_size": 10000 + i * 1000}}
        for i in range(100)
    ]

    print("\nExecuting 100 tasks in parallel...")
    start = time.time()
    results = cluster.execute_parallel(tasks, bitcoin_experiment)
    total_time = time.time() - start

    aggregated = network.aggregate_results(results)

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Total tasks: {aggregated['total_tasks']}")
    print(f"Successful: {aggregated['successful']}")
    print(f"Failed: {aggregated['failed']}")
    print(f"Success rate: {aggregated['success_rate']:.1f}%")
    print(f"Total time: {total_time:.2f}s")
    print(f"Throughput: {aggregated['total_tasks']/total_time:.1f} tasks/sec")

    cluster.shutdown()

    print("\nDEMO COMPLETE!")


if __name__ == "__main__":
    main()
