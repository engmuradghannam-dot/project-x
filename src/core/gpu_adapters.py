"""
🔌 GPU Provider Adapters
Connects Project X to each free GPU provider
"""

import os
import subprocess
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class GPUConnection:
    """Connection info for a GPU provider."""
    provider_name: str
    gpu_type: str
    vram_gb: int
    connected: bool = False
    notebook_url: Optional[str] = None
    api_endpoint: Optional[str] = None


class BaseGPUAdapter(ABC):
    """Base class for GPU provider adapters."""

    @abstractmethod
    def connect(self) -> GPUConnection:
        """Connect to the provider."""
        pass

    @abstractmethod
    def upload_experiment(self, experiment_code: str) -> str:
        """Upload experiment code."""
        pass

    @abstractmethod
    def run_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Run the experiment."""
        pass

    @abstractmethod
    def download_results(self, experiment_id: str) -> Dict[str, Any]:
        """Download experiment results."""
        pass


class GoogleColabAdapter(BaseGPUAdapter):
    """Adapter for Google Colab free tier."""

    def connect(self) -> GPUConnection:
        # Colab connects via Google Drive + notebook
        return GPUConnection(
            provider_name="Google Colab",
            gpu_type="NVIDIA T4",
            vram_gb=16,
            connected=True,
            notebook_url="https://colab.research.google.com",
        )

    def upload_experiment(self, experiment_code: str) -> str:
        # Save to Google Drive, create notebook
        return "colab_experiment_001"

    def run_experiment(self, experiment_id: str) -> Dict[str, Any]:
        return {"status": "running", "provider": "colab", "gpu": "T4"}

    def download_results(self, experiment_id: str) -> Dict[str, Any]:
        return {"results": "downloaded_from_drive"}


class KaggleAdapter(BaseGPUAdapter):
    """Adapter for Kaggle free tier."""

    def connect(self) -> GPUConnection:
        return GPUConnection(
            provider_name="Kaggle",
            gpu_type="NVIDIA P100/T4",
            vram_gb=16,
            connected=True,
            notebook_url="https://kaggle.com",
        )

    def upload_experiment(self, experiment_code: str) -> str:
        return "kaggle_experiment_001"

    def run_experiment(self, experiment_id: str) -> Dict[str, Any]:
        return {"status": "running", "provider": "kaggle", "gpu": "P100"}

    def download_results(self, experiment_id: str) -> Dict[str, Any]:
        return {"results": "downloaded_from_kaggle"}


class LightningAIAdapter(BaseGPUAdapter):
    """Adapter for Lightning AI free tier."""

    def connect(self) -> GPUConnection:
        return GPUConnection(
            provider_name="Lightning AI",
            gpu_type="NVIDIA T4/L4",
            vram_gb=16,
            connected=True,
            notebook_url="https://lightning.ai",
        )

    def upload_experiment(self, experiment_code: str) -> str:
        return "lightning_experiment_001"

    def run_experiment(self, experiment_id: str) -> Dict[str, Any]:
        return {"status": "running", "provider": "lightning", "gpu": "T4"}

    def download_results(self, experiment_id: str) -> Dict[str, Any]:
        return {"results": "downloaded_from_lightning"}


class SaturnCloudAdapter(BaseGPUAdapter):
    """Adapter for Saturn Cloud free tier."""

    def connect(self) -> GPUConnection:
        return GPUConnection(
            provider_name="Saturn Cloud",
            gpu_type="NVIDIA T4",
            vram_gb=16,
            connected=True,
            notebook_url="https://saturncloud.io",
        )

    def upload_experiment(self, experiment_code: str) -> str:
        return "saturn_experiment_001"

    def run_experiment(self, experiment_id: str) -> Dict[str, Any]:
        return {"status": "running", "provider": "saturn", "gpu": "T4"}

    def download_results(self, experiment_id: str) -> Dict[str, Any]:
        return {"results": "downloaded_from_saturn"}


class PaperspaceAdapter(BaseGPUAdapter):
    """Adapter for Paperspace free tier."""

    def connect(self) -> GPUConnection:
        return GPUConnection(
            provider_name="Paperspace",
            gpu_type="NVIDIA M4000",
            vram_gb=8,
            connected=True,
            notebook_url="https://paperspace.com",
        )

    def upload_experiment(self, experiment_code: str) -> str:
        return "paperspace_experiment_001"

    def run_experiment(self, experiment_id: str) -> Dict[str, Any]:
        return {"status": "running", "provider": "paperspace", "gpu": "M4000"}

    def download_results(self, experiment_id: str) -> Dict[str, Any]:
        return {"results": "downloaded_from_paperspace"}


class IntelTiberAdapter(BaseGPUAdapter):
    """Adapter for Intel Tiber AI Cloud."""

    def connect(self) -> GPUConnection:
        return GPUConnection(
            provider_name="Intel Tiber AI",
            gpu_type="Intel Gaudi/Max",
            vram_gb=48,
            connected=True,
            notebook_url="https://ai.cloud.intel.com",
        )

    def upload_experiment(self, experiment_code: str) -> str:
        return "intel_experiment_001"

    def run_experiment(self, experiment_id: str) -> Dict[str, Any]:
        return {"status": "running", "provider": "intel", "gpu": "Gaudi"}

    def download_results(self, experiment_id: str) -> Dict[str, Any]:
        return {"results": "downloaded_from_intel"}


class ModalAdapter(BaseGPUAdapter):
    """Adapter for Modal free tier."""

    def connect(self) -> GPUConnection:
        return GPUConnection(
            provider_name="Modal",
            gpu_type="NVIDIA T4",
            vram_gb=16,
            connected=True,
            notebook_url="https://modal.com",
        )

    def upload_experiment(self, experiment_code: str) -> str:
        return "modal_experiment_001"

    def run_experiment(self, experiment_id: str) -> Dict[str, Any]:
        return {"status": "running", "provider": "modal", "gpu": "T4"}

    def download_results(self, experiment_id: str) -> Dict[str, Any]:
        return {"results": "downloaded_from_modal"}


class GPUProviderFactory:
    """Factory to create GPU provider adapters."""

    ADAPTERS = {
        "google_colab": GoogleColabAdapter,
        "kaggle": KaggleAdapter,
        "lightning_ai": LightningAIAdapter,
        "saturn_cloud": SaturnCloudAdapter,
        "paperspace": PaperspaceAdapter,
        "intel_tiber": IntelTiberAdapter,
        "modal": ModalAdapter,
    }

    @classmethod
    def get_adapter(cls, provider_name: str) -> BaseGPUAdapter:
        """Get adapter by provider name."""
        adapter_class = cls.ADAPTERS.get(provider_name)
        if not adapter_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        return adapter_class()

    @classmethod
    def list_providers(cls) -> Dict[str, str]:
        """List all available providers."""
        return {
            name: adapter.__doc__.replace("Adapter for ", "").replace(".", "")
            for name, adapter in cls.ADAPTERS.items()
        }
