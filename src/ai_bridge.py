\"\"\"
AI Bridge - Direct Connection Between Kimi AI and Project X GPU System
This module allows Kimi (me) to directly control GPU experiments
\"\"\"

import json
import time
import re
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()


@dataclass
class AICommand:
    \"\"\"Command from AI to GPU system.\"\"\"
    command_id: str
    action: str  # 'run_experiment', 'spawn_gpu', 'get_status', 'benchmark'
    parameters: Dict[str, Any]
    timestamp: str
    priority: int = 1  # 1=normal, 2=high, 3=critical


@dataclass
class AIResponse:
    \"\"\"Response from GPU system to AI.\"\"\"
    command_id: str
    status: str  # 'success', 'failed', 'running'
    result: Dict[str, Any]
    execution_time: float
    gpu_used: str
    timestamp: str


class AIGPUBridge:
    \"\"\"
    AI-GPU Bridge

    Connects Kimi AI directly to the GPU virtualization system.
    Allows real-time experiment execution and monitoring.
    \"\"\"

    def __init__(self):
        self.command_queue: List[AICommand] = []
        self.response_log: List[AIResponse] = []
        self.active_experiments: Dict[str, Any] = {}
        self.is_connected = False

        # Lazy imports to avoid circular deps
        self.gpu_manager = None
        self.runner = None

        print("AI-GPU Bridge initialized")
        print("   Status: Ready for connection")

    def connect(self) -> bool:
        \"\"\"Connect to GPU system.\"\"\"
        try:
            from .gpu_virtualization.gpu_manager import GPUManager
            from .gpu_virtualization.experiment_runner import GPUExperimentRunner

            self.gpu_manager = GPUManager()
            self.runner = GPUExperimentRunner()
            self.is_connected = True

            console.print(Panel.fit(
                "[bold green]AI Connected to GPU System[/bold green]\n"
                "Kimi can now directly control GPU experiments",
                title="AI-GPU Bridge",
                border_style="green"
            ))
            return True
        except Exception as e:
            console.print(f"[red]Connection failed: {e}[/red]")
            return False

    def execute(self, action: str, **parameters) -> AIResponse:
        \"\"\"Execute a command directly.\"\"\"
        if not self.is_connected:
            self.connect()

        cmd_id = f"cmd_{int(time.time() * 1000)}"
        command = AICommand(
            command_id=cmd_id,
            action=action,
            parameters=parameters,
            timestamp=datetime.utcnow().isoformat(),
        )

        console.print(f"\n[bold cyan]AI Command:[/bold cyan] {action}")

        start = time.time()

        try:
            if action == "run_experiment":
                result = self._run_experiment(**parameters)
            elif action == "spawn_gpu":
                result = self._spawn_gpu(**parameters)
            elif action == "get_status":
                result = self._get_status()
            elif action == "benchmark":
                result = self._benchmark()
            elif action == "detect_gpus":
                result = self._detect_gpus()
            else:
                result = {"error": f"Unknown action: {action}"}

            status = "success"
        except Exception as e:
            result = {"error": str(e)}
            status = "failed"

        duration = time.time() - start

        response = AIResponse(
            command_id=cmd_id,
            status=status,
            result=result,
            execution_time=duration,
            gpu_used=self.runner.gpu.specs.name if self.runner and self.runner.gpu else "none",
            timestamp=datetime.utcnow().isoformat(),
        )

        self.response_log.append(response)

        console.print(f"   Status: {status}")
        console.print(f"   Time: {duration:.2f}s")

        return response

    def _run_experiment(self, name: str, experiment_type: str = "bitcoin", **kwargs) -> Dict[str, Any]:
        \"\"\"Run an experiment on GPU.\"\"\"
        if experiment_type == "bitcoin":
            from .experiments.registry import ExperimentRegistry

            # Auto-generate Bitcoin experiment if not exists
            if name not in ExperimentRegistry.get_all():
                self._create_bitcoin_experiment(name, **kwargs)

            return self.runner.run_experiment(name, ExperimentRegistry.get_all()[name], **kwargs)

        return {"error": f"Unknown experiment type: {experiment_type}"}

    def _create_bitcoin_experiment(self, name: str, sample_size: int = 10000, **kwargs) -> None:
        \"\"\"Create a Bitcoin experiment dynamically.\"\"\"
        from .experiments.registry import ExperimentRegistry

        @ExperimentRegistry.register(
            name=name,
            description=f"AI-generated Bitcoin experiment: {name}",
            tags=["bitcoin", "ai-generated"]
        )
        def ai_experiment(gpu=None, sample_size=10000, **params):
            import numpy as np

            # Allocate on GPU
            if gpu:
                keys = gpu.allocate((sample_size,), dtype=np.uint64)
                keys[:] = np.random.randint(0, 2**64, size=sample_size, dtype=np.uint64)

                # Compute features
                features = np.zeros((sample_size, 24), dtype=np.float32)
                for i in range(sample_size):
                    k = keys[i]
                    bytes_arr = np.array([(k >> (8*j)) & 0xFF for j in range(8)], dtype=np.float32)
                    features[i, 0] = np.mean(bytes_arr)
                    features[i, 1] = np.std(bytes_arr)
                    features[i, 2] = np.min(bytes_arr)
                    features[i, 3] = np.max(bytes_arr)

                gpu.free(keys)

                return {
                    "sample_size": sample_size,
                    "mean_feature_0": float(np.mean(features[:, 0])),
                    "std_feature_0": float(np.std(features[:, 0])),
                }

            return {"error": "No GPU available"}

    def _spawn_gpu(self, backend: str = "vast_ai", max_price: float = 3.0) -> Dict[str, Any]:
        \"\"\"Spawn a cloud GPU.\"\"\"
        from .gpu_virtualization.virtual_gpu import GPUBackend

        backend_map = {
            "vast": GPUBackend.VAST_AI,
            "runpod": GPUBackend.RUNPOD,
            "cpu": GPUBackend.CPU_RAM,
        }

        gpu_backend = backend_map.get(backend, GPUBackend.VAST_AI)
        gpu = self.gpu_manager.spawn_cloud(gpu_backend, max_price=max_price)

        if gpu:
            self.runner.gpu = gpu
            return {
                "gpu": gpu.specs.name,
                "vram": gpu.specs.vram_gb,
                "price": gpu.specs.price_per_hour,
            }

        return {"error": "Failed to spawn GPU"}

    def _get_status(self) -> Dict[str, Any]:
        \"\"\"Get system status.\"\"\"
        return {
            "connected": self.is_connected,
            "active_gpu": self.runner.gpu.specs.name if self.runner and self.runner.gpu else None,
            "queue_length": len(self.command_queue),
            "total_commands": len(self.response_log),
            "recent_responses": [asdict(r) for r in self.response_log[-5:]],
        }

    def _benchmark(self) -> Dict[str, Any]:
        \"\"\"Benchmark current GPU.\"\"\"
        if self.runner and self.runner.gpu:
            return self.runner.gpu.benchmark()
        return {"error": "No GPU active"}

    def _detect_gpus(self) -> Dict[str, Any]:
        \"\"\"Detect all available GPUs.\"\"\"
        return {
            name: {
                "available": status.available,
                "vram_gb": status.vram_gb,
                "is_free": status.is_free,
                "price": status.price_per_hour,
            }
            for name, status in self.gpu_manager.detect_all().items()
        }

    def chat_interface(self, user_message: str) -> str:
        \"\"\"
        Chat Interface - Parse natural language commands

        Examples:
        - "run bitcoin experiment with 100k samples"
        - "spawn H100 GPU"
        - "what GPUs are available?"
        - "benchmark current GPU"
        \"\"\"
        msg = user_message.lower()

        if "run" in msg and "experiment" in msg:
            # Extract sample size
            size_match = re.search(r'(\d+)[kK]', msg)
            sample_size = int(size_match.group(1)) * 1000 if size_match else 10000

            response = self.execute("run_experiment", name="ai_bitcoin_test", sample_size=sample_size)
            return f"Experiment complete! Result: {response.result}"

        elif "spawn" in msg or "create" in msg:
            gpu_type = "h100" if "h100" in msg else "vast"
            response = self.execute("spawn_gpu", backend=gpu_type)
            return f"GPU spawned! {response.result}"

        elif "available" in msg or "detect" in msg:
            response = self.execute("detect_gpus")
            gpus = response.result
            lines = ["Available GPUs:"]
            for name, info in gpus.items():
                icon = "OK" if info["available"] else "XX"
                free = " [FREE]" if info["is_free"] else f" [${info['price']}/hr]"
                lines.append(f"   {icon} {name}: {info['vram_gb']}GB{free}")
            return "\n".join(lines)

        elif "benchmark" in msg or "test" in msg:
            response = self.execute("benchmark")
            return f"Benchmark: {response.result}"

        elif "status" in msg:
            response = self.execute("get_status")
            return f"Status: {json.dumps(response.result, indent=2)}"

        else:
            return "AI-GPU Bridge Commands:\n- run bitcoin experiment with 100k samples\n- spawn H100 GPU\n- what GPUs are available?\n- benchmark current GPU\n- show status"


# Singleton instance
_bridge_instance = None

def get_bridge() -> AIGPUBridge:
    \"\"\"Get or create the AI-GPU bridge instance.\"\"\"
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = AIGPUBridge()
    return _bridge_instance
