"""
💾 MemoryPool - Manages System RAM as VRAM for Virtual GPU
"""

import numpy as np
import threading
from typing import Dict, Optional, Tuple
from collections import OrderedDict


class MemoryPool:
    """
    Manages a pool of system memory that acts as GPU VRAM.
    Uses LRU eviction policy when memory is full.
    """

    def __init__(self, size_gb: float = 64.0):
        self.size_bytes = int(size_gb * 1024**3)
        self.used_bytes = 0
        self.allocations: Dict[int, Tuple[np.ndarray, int]] = OrderedDict()
        self._lock = threading.Lock()

        print(f"💾 MemoryPool initialized: {size_gb} GB")

    def allocate(self, shape: tuple, dtype=np.float32) -> np.ndarray:
        """Allocate memory from the pool."""
        arr = np.empty(shape, dtype=dtype)
        size = arr.nbytes

        with self._lock:
            # Check if we need to evict
            while self.used_bytes + size > self.size_bytes and self.allocations:
                self._evict_oldest()

            if self.used_bytes + size > self.size_bytes:
                raise MemoryError("MemoryPool full, cannot allocate")

            arr_id = id(arr)
            self.allocations[arr_id] = (arr, size)
            self.used_bytes += size

        return arr

    def free(self, arr: np.ndarray) -> None:
        """Free memory back to the pool."""
        arr_id = id(arr)

        with self._lock:
            if arr_id in self.allocations:
                _, size = self.allocations.pop(arr_id)
                self.used_bytes -= size

    def _evict_oldest(self) -> None:
        """Evict oldest allocation (LRU)."""
        if self.allocations:
            arr_id, (_, size) = self.allocations.popitem(last=False)
            self.used_bytes -= size

    def get_stats(self) -> Dict[str, float]:
        """Get memory pool statistics."""
        return {
            "total_gb": self.size_bytes / 1024**3,
            "used_gb": self.used_bytes / 1024**3,
            "free_gb": (self.size_bytes - self.used_bytes) / 1024**3,
            "utilization": self.used_bytes / self.size_bytes * 100,
            "allocations": len(self.allocations),
        }
