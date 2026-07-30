\"\"\"
Project X - Advanced Experimentation Framework
Auto-connects GPU on startup
\"\"\"

__version__ = "0.1.0"
__author__ = "Murad Ghannam"

# Auto-connect GPU on module import
from .gpu_connector import ensure_gpu_connected, get_gpu, get_runner, get_bridge, check_gpu_status

# Ensure GPU is always ready
ensure_gpu_connected()

# Export main components
from .core.engine import ExperimentEngine
from .core.config import Config
from .core.logger import get_logger
from .experiments.runner import ExperimentRunner
from .experiments.registry import ExperimentRegistry
from .gpu_virtualization import VirtualGPU, GPUBackend, GPUManager
from .ai_bridge import AIGPUBridge
from .murad_ai import MuradAI

__all__ = [
    "ExperimentEngine",
    "Config",
    "get_logger",
    "ExperimentRunner",
    "ExperimentRegistry",
    "VirtualGPU",
    "GPUBackend",
    "GPUManager",
    "AIGPUBridge",
    "MuradAI",
    "ensure_gpu_connected",
    "get_gpu",
    "get_runner",
    "get_bridge",
    "check_gpu_status",
]
