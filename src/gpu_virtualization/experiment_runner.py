"""
🧪 Experiment Runner with GPU Support
Automatically uses best available GPU for experiments
"""

import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .core.config import Config
from .core.logger import get_logger
from .gpu_virtualization.gpu_manager import GPUManager
from .gpu_virtualization.virtual_gpu import VirtualGPU, GPUBackend

console = Console()
logger = get_logger(__name__)


class GPUExperimentRunner:
    """
    🔥 Experiment Runner with Automatic GPU Selection

    Features:
    - Auto-detects best free GPU
    - Falls back to CPU-RAM virtualization
    - Can spawn cloud GPU on demand
    - Tracks GPU utilization and cost
    """

    def __init__(self, config: Optional[Config] = None, force_gpu: Optional[str] = None):
        self.config = config or Config()
        self.gpu_manager = GPUManager()
        self.gpu: Optional[VirtualGPU] = None
        self.force_gpu = force_gpu
        self.experiment_cost = 0.0
        self.experiment_time = 0.0

        # Initialize GPU
        self._init_gpu()

    def _init_gpu(self) -> None:
        """Initialize GPU backend."""
        if self.force_gpu:
            # Use specified GPU
            backend_map = {
                "cpu": GPUBackend.CPU_RAM,
                "colab": GPUBackend.COLAB_T4,
                "kaggle": GPUBackend.KAGGLE_P100,
                "vast": GPUBackend.VAST_AI,
                "runpod": GPUBackend.RUNPOD,
            }
            backend = backend_map.get(self.force_gpu, GPUBackend.CPU_RAM)
            self.gpu = VirtualGPU(backend)
        else:
            # Auto-detect best GPU
            self.gpu = self.gpu_manager.get_best_free()

        if self.gpu:
            console.print(f"\n🖥️  [bold green]GPU Ready:[/bold green] {self.gpu.specs.name}")
            console.print(f"   VRAM: {self.gpu.specs.vram_gb} GB")
            console.print(f"   Cost: ${self.gpu.specs.price_per_hour}/hr")

    def run_experiment(self, name: str, experiment_func: Callable, **kwargs) -> Dict[str, Any]:
        """Run experiment with GPU acceleration."""
        if not self.gpu:
            raise RuntimeError("No GPU available")

        console.print(f"\n🔬 [bold cyan]Running: {name}[/bold cyan]")

        start_time = time.time()

        # Run experiment with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Executing {name}...", total=None)

            # Execute experiment
            try:
                result = experiment_func(gpu=self.gpu, **kwargs)
                status = "success"
            except Exception as e:
                result = {"error": str(e)}
                status = "failed"
                logger.error(f"Experiment {name} failed: {e}")

            progress.update(task, completed=True)

        duration = time.time() - start_time
        self.experiment_time += duration

        # Calculate cost
        if self.gpu.specs.price_per_hour > 0:
            cost = (duration / 3600) * self.gpu.specs.price_per_hour
            self.experiment_cost += cost

        # Get GPU utilization
        utilization = self.gpu.get_utilization()

        experiment_result = {
            "name": name,
            "status": status,
            "duration_seconds": duration,
            "gpu_used": self.gpu.specs.name,
            "vram_gb": self.gpu.specs.vram_gb,
            "gpu_utilization": utilization,
            "cost_usd": self.experiment_cost,
            "result": result,
        }

        console.print(f"\n📊 [bold]Results:[/bold]")
        console.print(f"   Status: {status}")
        console.print(f"   Duration: {duration:.2f}s")
        console.print(f"   Memory Used: {utilization['memory_used_gb']:.2f}/{utilization['memory_total_gb']:.2f} GB")
        console.print(f"   Cost: ${self.experiment_cost:.4f}")

        return experiment_result

    def run_with_fallback(self, name: str, experiment_func: Callable, **kwargs) -> Dict[str, Any]:
        """Run experiment with automatic fallback to CPU-RAM."""
        try:
            return self.run_experiment(name, experiment_func, **kwargs)
        except MemoryError as e:
            console.print(f"\n⚠️  [yellow]GPU OOM, falling back to CPU-RAM...[/yellow]")

            # Switch to CPU-RAM
            self.gpu = VirtualGPU(GPUBackend.CPU_RAM)
            return self.run_experiment(name, experiment_func, **kwargs)

    def benchmark_gpu(self) -> Dict[str, float]:
        """Benchmark current GPU."""
        if not self.gpu:
            raise RuntimeError("No GPU available")

        console.print(f"\n⚡ [bold]Benchmarking {self.gpu.specs.name}...[/bold]")
        return self.gpu.benchmark()

    def get_summary(self) -> Dict[str, Any]:
        """Get experiment summary."""
        return {
            "gpu": self.gpu.specs.name if self.gpu else None,
            "total_experiment_time": self.experiment_time,
            "total_cost_usd": self.experiment_cost,
            "backend": self.gpu.specs.backend.value if self.gpu else None,
        }

    def spawn_cloud_if_needed(self, min_vram_gb: float = 32.0) -> bool:
        """Spawn cloud GPU if current GPU is insufficient."""
        if not self.gpu:
            return False

        if self.gpu.specs.vram_gb >= min_vram_gb:
            return True

        console.print(f"\n🚀 [yellow]Current GPU ({self.gpu.specs.vram_gb}GB) insufficient, spawning cloud GPU...[/yellow]")

        # Try to spawn Vast.ai H100
        new_gpu = self.gpu_manager.spawn_cloud(GPUBackend.VAST_AI, max_price=3.0)
        if new_gpu:
            self.gpu = new_gpu
            return True

        return False


# Example experiment functions that use GPU
def bitcoin_key_analysis(gpu: VirtualGPU, sample_size: int = 10000, **kwargs) -> Dict[str, Any]:
    """Bitcoin key locality analysis using GPU."""
    import numpy as np

    # Allocate memory on GPU
    keys = gpu.allocate((sample_size,), dtype=np.uint64)

    # Generate random keys
    keys[:] = np.random.randint(0, 2**64, size=sample_size, dtype=np.uint64)

    # Extract features (GPU-accelerated)
    features = gpu.compute(extract_features_gpu, keys)

    # Compute distances
    distances = gpu.compute(compute_distances_gpu, features)

    # Free memory
    gpu.free(keys)

    return {
        "sample_size": sample_size,
        "mean_distance": float(np.mean(distances)),
        "std_distance": float(np.std(distances)),
    }


def extract_features_gpu(keys: np.ndarray) -> np.ndarray:
    """Extract features from keys (GPU-optimized)."""
    import numpy as np

    n = len(keys)
    features = np.zeros((n, 24), dtype=np.float32)

    # Byte statistics
    for i in range(n):
        k = keys[i]
        bytes_arr = np.array([(k >> (8*j)) & 0xFF for j in range(8)], dtype=np.float32)
        features[i, 0] = np.mean(bytes_arr)
        features[i, 1] = np.std(bytes_arr)
        features[i, 2] = np.min(bytes_arr)
        features[i, 3] = np.max(bytes_arr)
        features[i, 4] = np.sum(bytes_arr > 127)

    return features


def compute_distances_gpu(features: np.ndarray) -> np.ndarray:
    """Compute pairwise distances (GPU-optimized)."""
    import numpy as np

    n = len(features)
    distances = np.zeros((n, n), dtype=np.float32)

    for i in range(n):
        for j in range(i+1, n):
            dist = np.linalg.norm(features[i] - features[j])
            distances[i, j] = dist
            distances[j, i] = dist

    return distances
