"""
🔥 Project X - Core Module
Advanced Experimentation Framework
"""

__version__ = "0.1.0"
__author__ = "Murad Ghannam"
__email__ = "eng.murad.ghannam@gmail.com"

from .engine import ExperimentEngine
from .config import Config
from .logger import get_logger

__all__ = ["ExperimentEngine", "Config", "get_logger"]
