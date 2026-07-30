\"\"\"
GPUCluster - Manages 100 Parallel GPU Nodes
\"\"\"

import time
import uuid
import threading
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

from .cluster_node import ClusterNode, NodeStatus
from ..gpu_virtualization.virtual_gpu import GPUBackend

console = Console()


@dataclass
class ClusterConfig:
    \"\"\"Configuration for GPU cluster.\"\"\"
    num_nodes: int = 100
    vram_per_node_gb: float = 8.0  # Each node gets 8GB VRAM
    backend: GPUBackend = GPUBackend.CPU_RAM
    max_concurrent_tasks: int = 100


class GPUCluster:
    \"\"\"
    GPU Cluster - 100 Parallel GPU Instances

    Creates a network of GPU nodes that work simultaneously.
    Each node is a virtual GPU using CPU-RAM (or real GPU if available).
    \"\"\"

    def __init__(self, config: Optional[ClusterConfig] = None):
        self.config = config or ClusterConfig()
        self.nodes: Dict[str, ClusterNode] = {}
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self._lock = threading.Lock()

        print(f"\n{'='*70}")
        print(f"  GPU CLUSTER INITIALIZATION")
        print(f"  Nodes: {self.config.num_nodes}")
        print(f"  VRAM/Node: {self.config.vram_per_node_gb} GB")
        print(f"  Total VRAM: {self.config.num_nodes * self.config.vram_per_node_gb} GB")
        print(f"{'='*70}\n")

    def create_nodes(self) -> None:
        \"\"\"Create all cluster nodes.\"\"\"
        print("Creating nodes...")

        for i in range(self.config.num_nodes):
            node_id = f"node_{i:03d}"
            node = ClusterNode(
                node_id=node_id,
                backend=self.config.backend,
                vram_gb=self.config.vram_per_node_gb,
            )
            self.nodes[node_id] = node

        print(f"\nCreated {len(self.nodes)} nodes successfully!")

    def start_all(self) -> None:
        \"\"\"Start all nodes.\"\"\"
        print("\nStarting all nodes...")

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(node.start): node_id for node_id, node in self.nodes.items()}

            for future in as_completed(futures):
                node_id = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"  Node {node_id} failed to start: {e}")

        online = sum(1 for n in self.nodes.values() if n.status.is_online)
        print(f"\n  Online: {online}/{len(self.nodes)} nodes")

    def stop_all(self) -> None:
        \"\"\"Stop all nodes.\"\"\"
        print("\nStopping all nodes...")

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(node.stop): node_id for node_id, node in self.nodes.items()}

            for future in as_completed(futures):
                pass

        print("All nodes stopped.")

    def distribute_task(self, task_id: str, experiment_func: Callable, parameters: Dict[str, Any] = None) -> str:
        \"\"\"Distribute a task to the least busy node.\"\"\"
        # Find least busy node
        best_node = None
        min_queue = float('inf')

        for node in self.nodes.values():
            if not node.status.is_busy and node.status.is_online:
                queue_len = len(node.task_queue)
                if queue_len < min_queue:
                    min_queue = queue_len
                    best_node = node

        if best_node is None:
            # All busy, pick one with shortest queue
            for node in self.nodes.values():
                if node.status.is_online:
                    queue_len = len(node.task_queue)
                    if queue_len < min_queue:
                        min_queue = queue_len
                        best_node = node

        if best_node:
            best_node.submit_task(task_id, experiment_func, parameters)
            with self._lock:
                self.total_tasks += 1
            return best_node.node_id

        return None

    def run_parallel_experiments(self, experiments: List[Dict[str, Any]], show_progress: bool = True) -> List[Dict[str, Any]]:
        \"\"\"
        Run multiple experiments in parallel across all nodes.

        Args:
            experiments: List of experiment dicts with 'id', 'function', 'parameters'

        Returns:
            List of results from all experiments
        \"\"\"
        print(f"\n{'='*70}")
        print(f"  RUNNING {len(experiments)} EXPERIMENTS IN PARALLEL")
        print(f"  Nodes: {len(self.nodes)}")
        print(f"  Avg experiments/node: {len(experiments) / len(self.nodes):.1f}")
        print(f"{'='*70}\n")

        # Distribute tasks
        for exp in experiments:
            self.distribute_task(
                task_id=exp["id"],
                experiment_func=exp["function"],
                parameters=exp.get("parameters", {}),
            )

        # Wait for completion with progress bar
        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Running experiments...", total=len(experiments))

                all_results = []
                while len(all_results) < len(experiments):
                    for node in self.nodes.values():
                        results = node.get_results()
                        all_results.extend(results)

                    progress.update(task, completed=len(all_results))
                    time.sleep(0.5)
        else:
            # Wait without progress bar
            all_results = []
            while len(all_results) < len(experiments):
                for node in self.nodes.values():
                    results = node.get_results()
                    all_results.extend(results)
                time.sleep(0.5)

        # Update stats
        with self._lock:
            self.completed_tasks = sum(1 for r in all_results if r["status"] == "success")
            self.failed_tasks = sum(1 for r in all_results if r["status"] == "failed")

        print(f"\n  Complete: {self.completed_tasks}/{len(experiments)}")
        print(f"  Failed: {self.failed_tasks}")

        return all_results

    def get_cluster_status(self) -> Dict[str, Any]:
        \"\"\"Get status of entire cluster.\"\"\"
        online = sum(1 for n in self.nodes.values() if n.status.is_online)
        busy = sum(1 for n in self.nodes.values() if n.status.is_busy)
        idle = online - busy

        total_vram = sum(n.status.vram_gb for n in self.nodes.values())
        total_compute = sum(n.status.total_compute_time for n in self.nodes.values())
        total_tasks = sum(n.status.tasks_completed for n in self.nodes.values())

        return {
            "total_nodes": len(self.nodes),
            "online": online,
            "busy": busy,
            "idle": idle,
            "offline": len(self.nodes) - online,
            "total_vram_gb": total_vram,
            "total_compute_time": total_compute,
            "total_tasks_completed": total_tasks,
            "pending_tasks": self.total_tasks - self.completed_tasks - self.failed_tasks,
        }

    def print_status(self) -> None:
        \"\"\"Print cluster status table.\"\"\"
        status = self.get_cluster_status()

        table = Table(title="GPU Cluster Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Nodes", str(status["total_nodes"]))
        table.add_row("Online", str(status["online"]))
        table.add_row("Busy", str(status["busy"]))
        table.add_row("Idle", str(status["idle"]))
        table.add_row("Total VRAM", f"{status['total_vram_gb']:.0f} GB")
        table.add_row("Tasks Completed", str(status["total_tasks_completed"]))
        table.add_row("Pending Tasks", str(status["pending_tasks"]))

        console.print(table)

    def __enter__(self):
        \"\"\"Context manager entry.\"\"\"
        self.create_nodes()
        self.start_all()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        \"\"\"Context manager exit.\"\"\"
        self.stop_all()
        return False
