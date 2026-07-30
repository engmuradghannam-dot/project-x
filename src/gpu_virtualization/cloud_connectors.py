"""
☁️ Cloud Connectors - Interface with free and cheap GPU providers
"""

import os
import time
import json
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class CloudConnector(ABC):
    """Base class for cloud GPU connectors."""

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the cloud provider."""
        pass

    @abstractmethod
    def get_gpu(self) -> Optional[Dict[str, Any]]:
        """Get available GPU instance."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the cloud provider."""
        pass


class ColabConnector(CloudConnector):
    """
    🔵 Google Colab Connector
    Free T4 GPU (16GB VRAM)
    """

    def __init__(self):
        self.connected = False
        self.gpu_info = None

    def connect(self) -> bool:
        """Check if running in Colab and has GPU."""
        try:
            import google.colab
            # Check GPU
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                self.connected = True
                parts = result.stdout.strip().split(",")
                self.gpu_info = {
                    "name": parts[0].strip(),
                    "vram_mb": int(parts[1].strip().split()[0]),
                }
                return True
        except:
            pass
        return False

    def get_gpu(self) -> Optional[Dict[str, Any]]:
        if self.connected:
            return self.gpu_info
        return None

    def disconnect(self) -> None:
        self.connected = False


class KaggleConnector(CloudConnector):
    """
    🟣 Kaggle Connector
    Free P100/T4 GPU (16GB VRAM)
    """

    def __init__(self):
        self.connected = False

    def connect(self) -> bool:
        """Check if running in Kaggle."""
        if os.environ.get("KAGGLE_KERNEL_RUN_TYPE"):
            self.connected = True
            return True
        return False

    def get_gpu(self) -> Optional[Dict[str, Any]]:
        if self.connected:
            return {"name": "NVIDIA P100", "vram_mb": 16280}
        return None

    def disconnect(self) -> None:
        self.connected = False


class VastAIConnector(CloudConnector):
    """
    🟢 Vast.ai Connector
    Cheap spot GPU instances (H100 at ~$2/hr)
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("VAST_AI_API_KEY")
        self.connected = False
        self.instance_id = None

    def connect(self) -> bool:
        """Connect to Vast.ai API."""
        if not self.api_key:
            print("⚠️  Vast.ai API key not found. Set VAST_AI_API_KEY env var.")
            return False

        # Here you would make actual API call to Vast.ai
        # For now, simulate connection
        self.connected = True
        return True

    def search_instances(self, gpu_type: str = "RTX 4090", max_price: float = 0.50) -> list:
        """Search for available GPU instances."""
        if not self.connected:
            return []

        # Simulated search results
        return [
            {
                "id": "instance_001",
                "gpu": gpu_type,
                "price": 0.45,
                "vram_gb": 24,
                "location": "US-East",
            },
            {
                "id": "instance_002",
                "gpu": "RTX 3090",
                "price": 0.30,
                "vram_gb": 24,
                "location": "EU-West",
            },
        ]

    def create_instance(self, instance_id: str) -> bool:
        """Create a GPU instance."""
        if not self.connected:
            return False

        self.instance_id = instance_id
        print(f"🚀 Created Vast.ai instance: {instance_id}")
        return True

    def get_gpu(self) -> Optional[Dict[str, Any]]:
        if self.instance_id:
            return {"instance_id": self.instance_id, "provider": "vast_ai"}
        return None

    def disconnect(self) -> None:
        if self.instance_id:
            print(f"🛑 Destroying Vast.ai instance: {self.instance_id}")
            self.instance_id = None
        self.connected = False


class RunPodConnector(CloudConnector):
    """
    🟠 RunPod Connector
    Serverless GPU (H100 at $2.49/hr)
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RUNPOD_API_KEY")
        self.connected = False

    def connect(self) -> bool:
        if not self.api_key:
            print("⚠️  RunPod API key not found. Set RUNPOD_API_KEY env var.")
            return False
        self.connected = True
        return True

    def get_gpu(self) -> Optional[Dict[str, Any]]:
        if self.connected:
            return {"provider": "runpod", "status": "ready"}
        return None

    def disconnect(self) -> None:
        self.connected = False


class LightningAIConnector(CloudConnector):
    """
    ⚡ Lightning AI Connector
    Free tier with T4/A10G GPU
    """

    def __init__(self):
        self.connected = False

    def connect(self) -> bool:
        """Check Lightning AI availability."""
        # Lightning AI requires account setup
        # Check for credentials
        if os.getenv("LIGHTNING_AI_API_KEY"):
            self.connected = True
            return True
        return False

    def get_gpu(self) -> Optional[Dict[str, Any]]:
        if self.connected:
            return {"provider": "lightning_ai", "gpu": "T4", "free_credits": 15}
        return None

    def disconnect(self) -> None:
        self.connected = False
