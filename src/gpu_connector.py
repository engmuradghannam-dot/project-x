\"\"\"
Permanent GPU Connector - Always-on GPU for Project X
Auto-connects to best available GPU on system startup
\"\"\"

import os
import time
import atexit
import signal
import sys
from typing import Optional, Dict, Any
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()

# Global GPU instance - always available
_GLOBAL_GPU = None
_GLOBAL_RUNNER = None
_GLOBAL_BRIDGE = None


def ensure_gpu_connected() -> bool:
    \"\"\"
    Ensure GPU is always connected and ready.
    Call this before any GPU operation.
    \"\"\"
    global _GLOBAL_GPU, _GLOBAL_RUNNER, _GLOBAL_BRIDGE

    if _GLOBAL_GPU is not None and _GLOBAL_RUNNER is not None:
        # Already connected
        return True

    try:
        from .gpu_virtualization.gpu_manager import GPUManager
        from .gpu_virtualization.experiment_runner import GPUExperimentRunner
        from .ai_bridge import AIGPUBridge

        # Initialize GPU Manager
        manager = GPUManager()

        # Get best free GPU (auto-detect)
        gpu = manager.get_best_free()

        if gpu is None:
            # Fallback to CPU-RAM
            from .gpu_virtualization.virtual_gpu import VirtualGPU, GPUBackend
            gpu = VirtualGPU(GPUBackend.CPU_RAM)

        # Initialize runner
        runner = GPUExperimentRunner()
        runner.gpu = gpu

        # Initialize bridge
        bridge = AIGPUBridge()
        bridge.gpu_manager = manager
        bridge.runner = runner
        bridge.is_connected = True

        # Store globally
        _GLOBAL_GPU = gpu
        _GLOBAL_RUNNER = runner
        _GLOBAL_BRIDGE = bridge

        console.print(Panel.fit(
            f"[bold green]GPU Connected & Ready[/bold green]\n"
            f"GPU: {gpu.specs.name}\n"
            f"VRAM: {gpu.specs.vram_gb} GB\n"
            f"Backend: {gpu.specs.backend.value}",
            title="Project X GPU",
            border_style="green"
        ))

        return True

    except Exception as e:
        console.print(f"[red]GPU connection failed: {e}[/red]")
        return False


def get_gpu():
    \"\"\"Get the global GPU instance.\"\"\"
    global _GLOBAL_GPU
    if _GLOBAL_GPU is None:
        ensure_gpu_connected()
    return _GLOBAL_GPU


def get_runner():
    \"\"\"Get the global experiment runner.\"\"\"
    global _GLOBAL_RUNNER
    if _GLOBAL_RUNNER is None:
        ensure_gpu_connected()
    return _GLOBAL_RUNNER


def get_bridge():
    \"\"\"Get the global AI bridge.\"\"\"
    global _GLOBAL_BRIDGE
    if _GLOBAL_BRIDGE is None:
        ensure_gpu_connected()
    return _GLOBAL_BRIDGE


def check_gpu_status() -> Dict[str, Any]:
    \"\"\"Check if GPU is connected and healthy.\"\"\"
    global _GLOBAL_GPU

    if _GLOBAL_GPU is None:
        return {
            "connected": False,
            "status": "disconnected",
            "message": "GPU not initialized",
        }

    try:
        util = _GLOBAL_GPU.get_utilization()
        return {
            "connected": True,
            "status": "healthy",
            "gpu_name": _GLOBAL_GPU.specs.name,
            "vram_total_gb": _GLOBAL_GPU.specs.vram_gb,
            "vram_used_gb": util["memory_used_gb"],
            "vram_free_gb": util["memory_total_gb"] - util["memory_used_gb"],
            "utilization": util["memory_utilization"],
        }
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "message": str(e),
        }


def reconnect_gpu() -> bool:
    \"\"\"Force reconnect GPU.\"\"\"
    global _GLOBAL_GPU, _GLOBAL_RUNNER, _GLOBAL_BRIDGE

    # Reset globals
    _GLOBAL_GPU = None
    _GLOBAL_RUNNER = None
    _GLOBAL_BRIDGE = None

    return ensure_gpu_connected()


# Auto-connect on module import
_ = ensure_gpu_connected()
