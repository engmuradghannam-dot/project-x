\"\"\"
GPU Cluster - 100 Parallel GPU Instances
Creates a swarm of virtual GPUs working in parallel
\"\"\"

import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


@dataclass
class ClusterNode:
    \"\"\"A single GPU node in the cluster.\"\"\"
    node_id: int
    gpu_type: str
    vram_gb: float
    status: str = "idle"  # idle, busy, error
    current_task: Optional[str] = None
    total_tasks: int = 0


class GPUCluster:
    \"\"\"
    GPU Cluster - 100 Parallel GPU Instances

    Creates a swarm of virtual GPUs:
    - 50x CPU-RAM nodes (uses system RAM)
    - 30x Colab T4 nodes (simulated)
    - 15x Kaggle P100 nodes (simulated)
    - 5x Cloud H100 nodes (simulated)
    \"\"\"

    def __init__(self, num_nodes: int = 100):
        self.num_nodes = num_nodes
        self.nodes: List[ClusterNode] = []
        self.executor = ThreadPoolExecutor(max_workers=num_nodes)
        self.results: Dict[str, Any] = {}
        self._lock = threading.Lock()

        # Initialize nodes
        self._init_nodes()

        console.print(f"[bold green]GPU Cluster initialized: {num_nodes} nodes[/bold green]")

    def _init_nodes(self) -> None:
        \"\"\"Initialize cluster nodes.\"\"\"
        # Distribution: 50% CPU-RAM, 30% Colab, 15% Kaggle, 5% Cloud
        distribution = [
            (50, "CPU-RAM", 64.0),
            (30, "Colab-T4", 16.0),
            (15, "Kaggle-P100", 16.0),
            (5, "Cloud-H100", 80.0),
        ]

        node_id = 0
        for count, gpu_type, vram in distribution:
            for _ in range(count):
                if node_id >= self.num_nodes:
                    break
                self.nodes.append(ClusterNode(
                    node_id=node_id,
                    gpu_type=gpu_type,
                    vram_gb=vram,
                ))
                node_id += 1

    def get_available_nodes(self) -> List[ClusterNode]:
        \"\"\"Get nodes that are currently idle.\"\"\"
        return [n for n in self.nodes if n.status == "idle"]

    def get_node(self, node_id: int) -> Optional[ClusterNode]:
        \"\"\"Get a specific node.\"\"\"
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def execute_on_node(self, node_id: int, task_name: str, 
                        operation: Callable, *args, **kwargs) -> Dict[str, Any]:
        \"\"\"Execute a task on a specific node.\"\"\"
        node = self.get_node(node_id)
        if not node:
            return {"error": f"Node {node_id} not found"}

        with self._lock:
            node.status = "busy"
            node.current_task = task_name

        start = time.time()

        try:
            result = operation(node, *args, **kwargs)
            status = "success"
        except Exception as e:
            result = {"error": str(e)}
            status = "failed"

        duration = time.time() - start

        with self._lock:
            node.status = "idle"
            node.current_task = None
            node.total_tasks += 1

        return {
            "node_id": node_id,
            "node_type": node.gpu_type,
            "task": task_name,
            "status": status,
            "result": result,
            "duration": duration,
        }

    def execute_parallel(self, tasks: List[Dict[str, Any]], 
                         operation: Callable) -> List[Dict[str, Any]]:
        \"\"\"
        Execute tasks in parallel across all available nodes.

        Args:
            tasks: List of task dictionaries with 'name' and 'params'
            operation: Function to execute on each node
        \"\"\"
        available = self.get_available_nodes()

        if len(tasks) > len(available):
            console.print(f"[yellow]Warning: {len(tasks)} tasks but only {len(available)} nodes available[/yellow]")

        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:

            task_progress = progress.add_task(
                f"Executing {len(tasks)} tasks on {len(available)} nodes...",
                total=len(tasks)
            )

            # Submit all tasks
            futures = {}
            for i, task in enumerate(tasks):
                node = available[i % len(available)]
                future = self.executor.submit(
                    self.execute_on_node,
                    node.node_id,
                    task["name"],
                    operation,
                    **task.get("params", {})
                )
                futures[future] = task["name"]

            # Collect results
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    result = future.result()
                    results.append(result)

                    if result["status"] == "success":
                        console.print(f"   [green]✓[/green] {task_name} on Node-{result['node_id']} ({result['duration']:.2f}s)")
                    else:
                        console.print(f"   [red]✗[/red] {task_name} on Node-{result['node_id']}: {result['result']}")

                except Exception as e:
                    console.print(f"   [red]✗[/red] {task_name}: {e}")
                    results.append({
                        "task": task_name,
                        "status": "error",
                        "error": str(e),
                    })

                progress.update(task_progress, advance=1)

        return results

    def map_reduce(self, data: List[Any], 
                   map_func: Callable,
                   reduce_func: Callable) -> Any:
        \"\"\"
        Map-Reduce across cluster.

        1. Split data across nodes
        2. Map function on each chunk
        3. Reduce all results
        \"\"\"
        # Split data into chunks
        chunk_size = max(1, len(data) // len(self.nodes))
        chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

        console.print(f"[cyan]Map-Reduce: {len(data)} items → {len(chunks)} chunks[/cyan]")

        # Map phase
        tasks = [
            {"name": f"map_chunk_{i}", "params": {"chunk": chunk, "func": map_func}}
            for i, chunk in enumerate(chunks)
        ]

        def map_operation(node, chunk, func):
            return [func(item) for item in chunk]

        map_results = self.execute_parallel(tasks, map_operation)

        # Collect successful map results
        mapped_data = []
        for r in map_results:
            if r["status"] == "success":
                mapped_data.extend(r["result"])

        # Reduce phase
        console.print("[cyan]Reducing results...[/cyan]")
        final_result = reduce_func(mapped_data)

        return final_result

    def get_cluster_stats(self) -> Dict[str, Any]:
        \"\"\"Get cluster statistics.\"\"\"
        idle = sum(1 for n in self.nodes if n.status == "idle")
        busy = sum(1 for n in self.nodes if n.status == "busy")
        error = sum(1 for n in self.nodes if n.status == "error")

        total_vram = sum(n.vram_gb for n in self.nodes)

        return {
            "total_nodes": len(self.nodes),
            "idle": idle,
            "busy": busy,
            "error": error,
            "utilization": busy / len(self.nodes) * 100,
            "total_vram_gb": total_vram,
            "total_tasks_completed": sum(n.total_tasks for n in self.nodes),
        }

    def print_status(self) -> None:
        \"\"\"Print cluster status.\"\"\"
        stats = self.get_cluster_stats()

        console.print("\\n[bold]GPU Cluster Status[/bold]")
        console.print(f"   Total Nodes: {stats['total_nodes']}")
        console.print(f"   Idle: {stats['idle']}")
        console.print(f"   Busy: {stats['busy']}")
        console.print(f"   Error: {stats['error']}")
        console.print(f"   Utilization: {stats['utilization']:.1f}%")
        console.print(f"   Total VRAM: {stats['total_vram_gb']:.0f} GB")
        console.print(f"   Tasks Completed: {stats['total_tasks_completed']}")

    def shutdown(self) -> None:
        \"\"\"Shutdown cluster.\"\"\"
        self.executor.shutdown(wait=True)
        console.print("[yellow]GPU Cluster shutdown[/yellow]")
