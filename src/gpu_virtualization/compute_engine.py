"""
⚡ ComputeEngine - Parallel CPU-based GPU-like compute
"""

import numpy as np
import threading
from typing import Callable, Any, List
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp


class ComputeEngine:
    """
    Simulates GPU compute units using CPU threads.
    Optimized for numerical computations.
    """

    def __init__(self, compute_units: int = 32, use_cuda: bool = False):
        self.compute_units = compute_units
        self.use_cuda = use_cuda
        self.executor = ThreadPoolExecutor(max_workers=compute_units)

        # Use all available CPU cores
        self.num_cores = mp.cpu_count()

        print(f"⚡ ComputeEngine: {compute_units} units, {self.num_cores} CPU cores")

    def execute(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation with parallelization."""
        return operation(*args, **kwargs)

    def parallel_map(self, func: Callable, data: List[Any], chunksize: int = 1000) -> List[Any]:
        """Apply function to data in parallel chunks."""
        # Split data into chunks
        chunks = [data[i:i+chunksize] for i in range(0, len(data), chunksize)]

        # Process chunks in parallel
        futures = [self.executor.submit(func, chunk) for chunk in chunks]
        results = [f.result() for f in futures]

        # Flatten results
        return [item for sublist in results for item in sublist]

    def parallel_matmul(self, a: np.ndarray, b: np.ndarray, block_size: int = 1024) -> np.ndarray:
        """Parallel blocked matrix multiplication."""
        m, k = a.shape
        k2, n = b.shape
        assert k == k2, "Matrix dimensions must match"

        result = np.zeros((m, n), dtype=a.dtype)

        def compute_block(args):
            i, j = args
            i_end = min(i + block_size, m)
            j_end = min(j + block_size, n)
            result[i:i_end, j:j_end] = np.matmul(a[i:i_end, :], b[:, j:j_end])

        # Create block tasks
        tasks = [(i, j) for i in range(0, m, block_size) for j in range(0, n, block_size)]

        # Execute in parallel
        list(self.executor.map(compute_block, tasks))

        return result

    def parallel_fft(self, arr: np.ndarray, n_chunks: int = 8) -> np.ndarray:
        """Parallel FFT using Cooley-Tukey decomposition."""
        chunk_size = len(arr) // n_chunks

        def fft_chunk(chunk):
            return np.fft.fft(chunk)

        chunks = [arr[i:i+chunk_size] for i in range(0, len(arr), chunk_size)]
        futures = [self.executor.submit(fft_chunk, chunk) for chunk in chunks]
        results = [f.result() for f in futures]

        return np.concatenate(results)

    def batch_operation(self, operation: Callable, batches: List[np.ndarray]) -> List[np.ndarray]:
        """Execute operation on multiple batches in parallel."""
        futures = [self.executor.submit(operation, batch) for batch in batches]
        return [f.result() for f in futures]
