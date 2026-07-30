\"\"\"
ClusterNode - Single GPU Node in the Cluster
Each node = 1 GPU instance (can be virtual, colab, kaggle, or cloud)
\"\"\"

import time
import uuid
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from ..gpu_virtualization.virtual_gpu import VirtualGPU, GPUBackend
from ..gpu_virtualization.gpu_manager import GPUManager


@dataclass
class NodeStatus:
    \"\"\"Status of a cluster node.\"\"\"
    node_id: str
    gpu_name: str
    vram_gb: float
    is_busy: bool = False
    current_task: Optional[str] = None
    tasks_completed: int = 0
    total_compute_time: float = 0.0
    last_heartbeat: Optional[str] = None
    is_online: bool = True


class ClusterNode:
    \"\"\"
    Single GPU Node

    Each node manages one GPU instance and executes tasks.
    Can be:
    - CPU-RAM virtual GPU
    - Google Colab T4
    - Kaggle P100
    - Cloud GPU (Vast.ai, RunPod)
    \"\"\"

    def __init__(self, node_id: str, backend: GPUBackend = GPUBackend.CPU_RAM, vram_gb: Optional[float] = None):
        self.node_id = node_id
        self.backend = backend

        # Initialize GPU
        self.gpu = VirtualGPU(backend, vram_gb=vram_gb)

        # Status
        self.status = NodeStatus(
            node_id=node_id,
            gpu_name=self.gpu.specs.name,
            vram_gb=self.gpu.specs.vram_gb,
        )

        # Task queue
        self.task_queue = []
        self.results = []
        self._lock = threading.Lock()
        self._worker_thread = None
        self._running = False

        print(f"  Node {node_id}: {self.gpu.specs.name} ({self.gpu.specs.vram_gb}GB) - READY")

    def start(self) -> None:
        \"\"\"Start the node worker thread.\"\"\"
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        self.status.is_online = True

    def stop(self) -> None:
        \"\"\"Stop the node.\"\"\"
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        self.status.is_online = False

    def _worker_loop(self) -> None:
        \"\"\"Worker loop - process tasks from queue.\"\"\"
        while self._running:
            task = None

            with self._lock:
                if self.task_queue:
                    task = self.task_queue.pop(0)

            if task:
                self._execute_task(task)
            else:
                time.sleep(0.1)  # Small sleep to prevent CPU spinning

    def _execute_task(self, task: Dict[str, Any]) -> None:
        \"\"\"Execute a single task.\"\"\"
        task_id = task["task_id"]
        experiment_func = task["function"]
        params = task.get("parameters", {})

        # Update status
        self.status.is_busy = True
        self.status.current_task = task_id
        self.status.last_heartbeat = datetime.utcnow().isoformat()

        start = time.time()

        try:
            # Execute with GPU
            result = experiment_func(gpu=self.gpu, **params)
            status = "success"
        except Exception as e:
            result = {"error": str(e)}
            status = "failed"

        duration = time.time() - start

        # Store result
        with self._lock:
            self.results.append({
                "task_id": task_id,
                "status": status,
                "result": result,
                "duration": duration,
                "node_id": self.node_id,
            })
            self.status.tasks_completed += 1
            self.status.total_compute_time += duration

        # Update status
        self.status.is_busy = False
        self.status.current_task = None
        self.status.last_heartbeat = datetime.utcnow().isoformat()

    def submit_task(self, task_id: str, experiment_func: Callable, parameters: Dict[str, Any] = None) -> None:
        \"\"\"Submit a task to this node.\"\"\"
        with self._lock:
            self.task_queue.append({
                "task_id": task_id,
                "function": experiment_func,
                "parameters": parameters or {},
            })

    def get_results(self) -> list:
        \"\"\"Get completed results.\"\"\"
        with self._lock:
            results = self.results.copy()
            self.results = []
            return results

    def get_status(self) -> NodeStatus:
        \"\"\"Get current node status.\"\"\"
        return self.status
