#!/usr/bin/env python3
"""
GPU Cluster Demo - 100 Parallel GPU Nodes
Shows how to run experiments across 100 GPU instances
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.gpu_cluster.parallel_experiment import ParallelExperimentRunner


def main():
    print("=" * 70)
    print("  PROJECT X - 100 GPU CLUSTER DEMO")
    print("=" * 70)

    # Create runner with 100 nodes
    print("\n[1] Initializing 100 GPU nodes...")
    runner = ParallelExperimentRunner(num_nodes=100)

    # Run MuradEngine Test 7 (Scaling)
    print("\n[2] Running MuradEngine Test 7 (Scaling)")
    print("    Target: 100,000 keys across 100 nodes")
    print("    Each node: 1,000 keys")

    results = runner.run_muradengine_test7(
        total_keys=100000,
        keys_per_node=1000
    )

    # Generate report
    print("\n[3] Generating report...")
    report = runner.generate_report(results, "MuradEngine Test 7")
    print(report)

    # Save report
    with open("test7_parallel_report.txt", "w") as f:
        f.write(report)

    print("\n[4] Report saved to: test7_parallel_report.txt")

    # Show Bitcoin batch example
    print("\n[5] Running Bitcoin analysis (1M samples)...")
    btc_results = runner.run_bitcoin_batch(
        total_samples=1000000,
        samples_per_node=10000
    )

    btc_report = runner.generate_report(btc_results, "Bitcoin Analysis")
    print(btc_report)

    with open("bitcoin_parallel_report.txt", "w") as f:
        f.write(btc_report)

    print("\n" + "=" * 70)
    print("  DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
