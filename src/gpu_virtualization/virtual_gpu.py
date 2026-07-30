"""
🖥️ VirtualGPU - Uses System RAM as VRAM for GPU-like compute
"""

import numpy as np
import threading
import time
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor
import psutil

from .memory_pool import MemoryPool
from .compute_engine import ComputeEngine


class GPUBackend(Enum):
    """Available GPU backends."""
    CPU_RAM = "cpu_ram"           # Use system RAM as VRAM
    COLAB_T4 = "colab_t4"         # Google Colab T4 (free)
    KAGGLE_P100 = "kaggle_p100"   # Kaggle P100 (free)
    LIGHTNING_AI = "lightning_ai" # Lightning AI (free tier)
    VAST_AI = "vast_ai"           # Vast.ai (cheap spot)
    RUNPOD = "runpod"             # RunPod (cheap)
    AWS_G4 = "aws_g4"             # AWS G4dn (credits)
    AZURE_NC = "azure_nc"         # Azure NC (credits)
    LOCAL_CUDA = "local_cuda"     # Local NVIDIA GPU


@dataclass
class GPUSpecs:
    """GPU specifications."""
    name: str
    vram_gb: float
    compute_units: int
    memory_bandwidth_gbps: float
    cuda_cores: int
    backend: GPUBackend
    is_free: bool = False
    price_per_hour: float = 0.0


# Predefined GPU specifications
GPU_CATALOG = {
    GPUBackend.CPU_RAM: GPUSpecs(
        name="Virtual-CPU-RAM",
        vram_gb=64.0,  # Uses 64GB of system RAM
        compute_units=32,
        memory_bandwidth_gbps=100.0,
        cuda_cores=0,
        backend=GPUBackend.CPU_RAM,
        is_free=True,
        price_per_hour=0.0,
    ),
    GPUBackend.COLAB_T4: GPUSpecs(
        name="NVIDIA T4 (Colab)",
        vram_gb=16.0,
        compute_units=40,
        memory_bandwidth_gbps=320.0,
        cuda_cores=2560,
        backend=GPUBackend.COLAB_T4,
        is_free=True,
        price_per_hour=0.0,
    ),
    GPUBackend.KAGGLE_P100: GPUSpecs(
        name="NVIDIA P100 (Kaggle)",
        vram_gb=16.0,
        compute_units=56,
        memory_bandwidth_gbps=732.0,
        cuda_cores=3584,
        backend=GPUBackend.KAGGLE_P100,
        is_free=True,
        price_per_hour=0.0,
    ),
    GPUBackend.VAST_AI: GPUSpecs(
        name="NVIDIA H100 (Vast.ai Spot)",
        vram_gb=80.0,
        compute_units=132,
        memory_bandwidth_gbps=3350.0,
        cuda_cores=16896,
        backend=GPUBackend.VAST_AI,
        is_free=False,
        price_per_hour=2.0,
    ),
    GPUBackend.RUNPOD: GPUSpecs(
        name="NVIDIA H100 (RunPod)",
        vram_gb=80.0,
        compute_units=132,
        memory_bandwidth_gbps=3350.0,
        cuda_cores=16896,
        backend=GPUBackend.RUNPOD,
        is_free=False,
        price_per_hour=2.49,
    ),
    GPUBackend.AWS_G4: GPUSpecs(
        name="NVIDIA T4 (AWS G4dn)",
        vram_gb=16.0,
        compute_units=40,
        memory_bandwidth_gbps=320.0,
        cuda_cores=2560,
        backend=GPUBackend.AWS_G4,
        is_free=False,
        price_per_hour=0.53,
    ),
    GPUBackend.LOCAL_CUDA: GPUSpecs(
        name="Local NVIDIA GPU",
        vram_gb=24.0,
        compute_units=82,
        memory_bandwidth_gbps=936.0,
        cuda_cores=5888,
        backend=GPUBackend.LOCAL_CUDA,
        is_free=True,
        price_per_hour=0.0,
    ),
}


class VirtualGPU:
    """
    🔥 Virtual GPU that uses system RAM as VRAM
    Simulates GPU compute on CPU with multi-threading
    Auto-detects and uses real CUDA if available
    """

    def __init__(self, backend: GPUBackend = GPUBackend.CPU_RAM, vram_gb: Optional[float] = None):
        self.backend = backend
        self.specs = GPU_CATALOG[backend]

        # Override VRAM if specified
        if vram_gb:
            self.specs.vram_gb = vram_gb

        # Initialize memory pool (uses system RAM)
        self.memory_pool = MemoryPool(size_gb=self.specs.vram_gb)

        # Initialize compute engine
        self.compute_engine = ComputeEngine(
            compute_units=self.specs.compute_units,
            use_cuda=self._has_cuda()
        )

        # Thread pool for parallel compute
        self.executor = ThreadPoolExecutor(max_workers=self.specs.compute_units)

        # Metrics
        self.metrics = {
            "total_compute_time": 0.0,
            "total_operations": 0,
            "memory_used_gb": 0.0,
        }

        self._lock = threading.Lock()

        print(f"🖥️  VirtualGPU initialized: {self.specs.name}")
        print(f"   VRAM: {self.specs.vram_gb} GB (System RAM)")
        print(f"   Compute Units: {self.specs.compute_units}")
        print(f"   CUDA Available: {self._has_cuda()}")

    def _has_cuda(self) -> bool:
        """Check if CUDA is available."""
        try:
            import cupy as cp
            return cp.cuda.runtime.getDeviceCount() > 0
        except:
            return False

    def allocate(self, shape: tuple, dtype=np.float32) -> np.ndarray:
        """Allocate memory on virtual GPU (system RAM)."""
        size_bytes = np.prod(shape) * np.dtype(dtype).itemsize
        size_gb = size_bytes / (1024**3)

        if size_gb > self.specs.vram_gb:
            raise MemoryError(
                f"Allocation of {size_gb:.2f} GB exceeds VRAM limit of {self.specs.vram_gb} GB"
            )

        # Allocate from memory pool
        arr = self.memory_pool.allocate(shape, dtype)

        with self._lock:
            self.metrics["memory_used_gb"] += size_gb

        return arr

    def free(self, arr: np.ndarray) -> None:
        """Free memory from virtual GPU."""
        size_bytes = arr.nbytes
        size_gb = size_bytes / (1024**3)

        self.memory_pool.free(arr)

        with self._lock:
            self.metrics["memory_used_gb"] -= size_gb

    def compute(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute compute operation on virtual GPU."""
        start = time.time()

        # Use CUDA if available
        if self._has_cuda() and self.backend != GPUBackend.CPU_RAM:
            result = self._cuda_compute(operation, *args, **kwargs)
        else:
            # CPU-based compute with threading
            result = self._cpu_compute(operation, *args, **kwargs)

        duration = time.time() - start

        with self._lock:
            self.metrics["total_compute_time"] += duration
            self.metrics["total_operations"] += 1

        return result

    def _cpu_compute(self, operation: Callable, *args, **kwargs) -> Any:
        """CPU-based parallel compute."""
        return self.compute_engine.execute(operation, *args, **kwargs)

    def _cuda_compute(self, operation: Callable, *args, **kwargs) -> Any:
        """CUDA-based compute."""
        import cupy as cp

        # Convert numpy arrays to cupy
        cupy_args = []
        for arg in args:
            if isinstance(arg, np.ndarray):
                cupy_args.append(cp.asarray(arg))
            else:
                cupy_args.append(arg)

        # Execute on GPU
        result = operation(*cupy_args, **kwargs)

        # Convert back to numpy
        if isinstance(result, cp.ndarray):
            result = cp.asnumpy(result)

        return result

    def matmul(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Matrix multiplication optimized for virtual GPU."""
        if self._has_cuda() and self.backend != GPUBackend.CPU_RAM:
            import cupy as cp
            a_gpu = cp.asarray(a)
            b_gpu = cp.asarray(b)
            result = cp.matmul(a_gpu, b_gpu)
            return cp.asnumpy(result)
        else:
            # Use optimized BLAS
            return np.matmul(a, b)

    def fft(self, arr: np.ndarray) -> np.ndarray:
        """Fast Fourier Transform."""
        if self._has_cuda() and self.backend != GPUBackend.CPU_RAM:
            import cupy as cp
            arr_gpu = cp.asarray(arr)
            result = cp.fft.fft(arr_gpu)
            return cp.asnumpy(result)
        else:
            return np.fft.fft(arr)

    def get_utilization(self) -> Dict[str, float]:
        """Get current GPU utilization."""
        return {
            "memory_used_gb": self.metrics["memory_used_gb"],
            "memory_total_gb": self.specs.vram_gb,
            "memory_utilization": self.metrics["memory_used_gb"] / self.specs.vram_gb * 100,
            "compute_utilization": min(100.0, self.metrics["total_operations"] / max(1, self.metrics["total_compute_time"]) * 10),
        }

    def benchmark(self) -> Dict[str, float]:
        """Run quick benchmark."""
        print("⚡ Running benchmark...")

        # Matrix multiplication benchmark
        size = 4096
        a = np.random.randn(size, size).astype(np.float32)
        b = np.random.randn(size, size).astype(np.float32)

        start = time.time()
        result = self.matmul(a, b)
        matmul_time = time.time() - start

        # FFT benchmark
        arr = np.random.randn(size * size).astype(np.float32)
        start = time.time()
        result = self.fft(arr)
        fft_time = time.time() - start

        return {
            "matmul_4096_time": matmul_time,
            "fft_16m_time": fft_time,
            "backend": self.specs.name,
            "vram_gb": self.specs.vram_gb,
        }

    def __del__(self):
        """Cleanup."""
        self.executor.shutdown(wait=True)
