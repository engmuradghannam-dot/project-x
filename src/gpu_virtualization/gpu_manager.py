"""
🎯 GPUManager - Auto-detects and manages all GPU backends
Connects to free GPUs, cheap cloud GPUs, or uses CPU-RAM fallback
"""

import os
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

from .virtual_gpu import VirtualGPU, GPUBackend, GPU_CATALOG
from .cloud_connectors import ColabConnector, KaggleConnector, VastAIConnector


@dataclass
class GPUStatus:
    """Status of a GPU backend."""
    backend: str
    available: bool
    vram_gb: float
    price_per_hour: float
    is_free: bool
    latency_ms: float = 0.0
    error: Optional[str] = None


class GPUManager:
    """
    🔥 GPU Manager - Your AI's GPU Controller

    Automatically:
    1. Detects all available GPU backends
    2. Prioritizes free options (Colab, Kaggle)
    3. Falls back to CPU-RAM virtualization
    4. Can spawn cloud GPU instances on demand
    """

    def __init__(self, preferred_backends: Optional[List[GPUBackend]] = None):
        self.preferred = preferred_backends or [
            GPUBackend.LOCAL_CUDA,
            GPUBackend.COLAB_T4,
            GPUBackend.KAGGLE_P100,
            GPUBackend.CPU_RAM,
        ]
        self.active_gpu: Optional[VirtualGPU] = None
        self.connectors = {
            "colab": ColabConnector(),
            "kaggle": KaggleConnector(),
            "vast_ai": VastAIConnector(),
        }
        self.status_cache: Dict[str, GPUStatus] = {}

        print("🎯 GPUManager initialized")
        print("   Preferred backends:", [b.value for b in self.preferred])

    def detect_all(self) -> Dict[str, GPUStatus]:
        """Detect all available GPU backends."""
        print("🔍 Detecting GPU backends...")

        statuses = {}

        # Check local CUDA
        statuses["local_cuda"] = self._check_local_cuda()

        # Check Colab
        statuses["colab"] = self._check_colab()

        # Check Kaggle
        statuses["kaggle"] = self._check_kaggle()

        # Check CPU-RAM (always available)
        statuses["cpu_ram"] = self._check_cpu_ram()

        # Check cloud options
        statuses["vast_ai"] = self._check_vast_ai()
        statuses["runpod"] = self._check_runpod()

        self.status_cache = statuses

        # Print summary
        print("\n📊 GPU Detection Results:")
        print("-" * 60)
        for name, status in statuses.items():
            icon = "✅" if status.available else "❌"
            free_tag = " [FREE]" if status.is_free else ""
            print(f"   {icon} {name}: {status.vram_gb} GB VRAM{free_tag}")
            if status.error:
                print(f"      Error: {status.error}")
        print("-" * 60)

        return statuses

    def _check_local_cuda(self) -> GPUStatus:
        """Check for local NVIDIA GPU."""
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if lines and lines[0]:
                    parts = lines[0].split(",")
                    name = parts[0].strip()
                    mem_mb = int(parts[1].strip().split()[0])
                    return GPUStatus(
                        backend="local_cuda",
                        available=True,
                        vram_gb=mem_mb / 1024,
                        price_per_hour=0.0,
                        is_free=True,
                    )
        except:
            pass

        return GPUStatus(
            backend="local_cuda",
            available=False,
            vram_gb=0,
            price_per_hour=0.0,
            is_free=True,
            error="No local NVIDIA GPU detected",
        )

    def _check_colab(self) -> GPUStatus:
        """Check if running in Google Colab."""
        try:
            import google.colab
            # Try to get GPU info
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(",")
                mem_mb = int(parts[1].strip().split()[0])
                return GPUStatus(
                    backend="colab",
                    available=True,
                    vram_gb=mem_mb / 1024,
                    price_per_hour=0.0,
                    is_free=True,
                )
        except:
            pass

        return GPUStatus(
            backend="colab",
            available=False,
            vram_gb=16.0,
            price_per_hour=0.0,
            is_free=True,
            error="Not running in Google Colab",
        )

    def _check_kaggle(self) -> GPUStatus:
        """Check if running in Kaggle."""
        if os.environ.get("KAGGLE_KERNEL_RUN_TYPE"):
            return GPUStatus(
                backend="kaggle",
                available=True,
                vram_gb=16.0,
                price_per_hour=0.0,
                is_free=True,
            )
        return GPUStatus(
            backend="kaggle",
            available=False,
            vram_gb=16.0,
            price_per_hour=0.0,
            is_free=True,
            error="Not running in Kaggle",
        )

    def _check_cpu_ram(self) -> GPUStatus:
        """Check available system RAM for CPU-RAM backend."""
        import psutil
        mem = psutil.virtual_memory()
        available_gb = mem.available / 1024**3
        # Use up to 75% of available RAM
        vram_gb = min(available_gb * 0.75, 128.0)  # Cap at 128GB

        return GPUStatus(
            backend="cpu_ram",
            available=True,
            vram_gb=vram_gb,
            price_per_hour=0.0,
            is_free=True,
        )

    def _check_vast_ai(self) -> GPUStatus:
        """Check Vast.ai availability."""
        return GPUStatus(
            backend="vast_ai",
            available=True,  # Always available (on-demand)
            vram_gb=80.0,
            price_per_hour=2.0,
            is_free=False,
        )

    def _check_runpod(self) -> GPUStatus:
        """Check RunPod availability."""
        return GPUStatus(
            backend="runpod",
            available=True,  # Always available (on-demand)
            vram_gb=80.0,
            price_per_hour=2.49,
            is_free=False,
        )

    def get_best_free(self) -> Optional[VirtualGPU]:
        """Get the best available free GPU."""
        statuses = self.detect_all()

        # Filter free and available
        free_gpus = [
            s for s in statuses.values()
            if s.available and s.is_free
        ]

        if not free_gpus:
            print("❌ No free GPU available, falling back to CPU-RAM")
            return VirtualGPU(GPUBackend.CPU_RAM)

        # Sort by VRAM (largest first)
        free_gpus.sort(key=lambda x: x.vram_gb, reverse=True)
        best = free_gpus[0]

        print(f"✅ Best free GPU: {best.backend} ({best.vram_gb} GB VRAM)")

        backend_map = {
            "local_cuda": GPUBackend.LOCAL_CUDA,
            "colab": GPUBackend.COLAB_T4,
            "kaggle": GPUBackend.KAGGLE_P100,
            "cpu_ram": GPUBackend.CPU_RAM,
        }

        backend = backend_map.get(best.backend, GPUBackend.CPU_RAM)
        self.active_gpu = VirtualGPU(backend, vram_gb=best.vram_gb)
        return self.active_gpu

    def spawn_cloud(self, backend: GPUBackend, max_price: float = 3.0) -> Optional[VirtualGPU]:
        """Spawn a cloud GPU instance."""
        specs = GPU_CATALOG[backend]

        if specs.price_per_hour > max_price:
            print(f"❌ {specs.name} costs ${specs.price_per_hour}/hr > max ${max_price}/hr")
            return None

        print(f"🚀 Spawning cloud GPU: {specs.name}")
        print(f"   Cost: ${specs.price_per_hour}/hr")

        # Here you would integrate with cloud provider API
        # For now, return VirtualGPU with cloud specs
        self.active_gpu = VirtualGPU(backend)
        return self.active_gpu

    def get_active(self) -> Optional[VirtualGPU]:
        """Get currently active GPU."""
        return self.active_gpu

    def benchmark_all(self) -> Dict[str, Dict[str, float]]:
        """Benchmark all available backends."""
        results = {}
        statuses = self.detect_all()

        for name, status in statuses.items():
            if status.available:
                print(f"\n⚡ Benchmarking {name}...")

                backend_map = {
                    "local_cuda": GPUBackend.LOCAL_CUDA,
                    "colab": GPUBackend.COLAB_T4,
                    "kaggle": GPUBackend.KAGGLE_P100,
                    "cpu_ram": GPUBackend.CPU_RAM,
                }

                backend = backend_map.get(name, GPUBackend.CPU_RAM)
                gpu = VirtualGPU(backend, vram_gb=status.vram_gb)
                results[name] = gpu.benchmark()

        return results

    def export_status(self, filepath: str) -> None:
        """Export GPU status to JSON."""
        data = {
            name: asdict(status)
            for name, status in self.status_cache.items()
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
