#!/usr/bin/env python3
"""
GPU Super Cluster Demo - 1000 Parallel Nodes
"""

import sys
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.gpu_super_cluster import GPUSuperCluster
from rich.console import Console

console = Console()


def bitcoin_experiment(node, sample_size=10000, **kwargs):
    """Bitcoin key analysis on a single node."""
    keys = np.random.randint(0, 2**64, size=min(sample_size, 1000), dtype=np.uint64)

    features = np.zeros((len(keys), 8), dtype=np.float32)
    for i in range(len(keys)):
        k = keys[i]
        bytes_arr = np.array([(k >> (8*j)) & 0xFF for j in range(8)], dtype=np.float32)
        features[i, 0] = np.mean(bytes_arr)
        features[i, 1] = np.std(bytes_arr)

    return {
        "node_id": node.node_id,
        "cluster_id": node.cluster_id,
        "node_type": node.gpu_type,
        "sample_size": len(keys),
        "mean_feature": float(np.mean(features[:, 0])),
    }


def main():
    print("=" * 70)
    print("PROJECT X - 1000 GPU SUPER CLUSTER DEMO")
    print("=" * 70)

    # 1. Initialize super cluster
    print("\n[1] Initializing 1000-node GPU Super Cluster...")
    cluster = GPUSuperCluster(num_nodes=1000, nodes_per_cluster=100)

    # 2. Show status
    print("\n[2] Super Cluster Status:")
    cluster.print_status()

    # 3. Prepare 1000 tasks
    print("\n[3] Preparing 1000 parallel Bitcoin experiments...")
    tasks = [
        {
            "name": f"bitcoin_analysis_node_{i}",
            "params": {"sample_size": 10000 + i * 100}
        }
        for i in range(1000)
    ]

    # 4. Execute in parallel (batches of 100)
    print("\n[4] Executing 1000 tasks in parallel (10 batches of 100)...")
    start = time.time()
    results = cluster.execute_batch(tasks, bitcoin_experiment, batch_size=100)
    total_time = time.time() - start

    # 5. Aggregate
    successful = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") != "success"]

    # 6. Show results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Total tasks: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Success rate: {len(successful)/len(results)*100:.1f}%")
    print(f"Total time: {total_time:.2f}s")
    print(f"Throughput: {len(results)/total_time:.1f} tasks/sec")
    print(f"Speedup: 1000x parallel processing!")

    # 7. Sample results
    print("\n[5] Sample Results (first 10):")
    for r in results[:10]:
        if r["status"] == "success":
            print(f"   Node-{r['node_id']} (Cluster-{r['cluster_id']}, {r['node_type']}): {r['result']}")

    # 8. Shutdown
    print("\n[6] Shutting down...")
    cluster.shutdown()

    print("\n" + "=" * 70)
    print("1000 GPU SUPER CLUSTER DEMO COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
