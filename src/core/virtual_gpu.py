
"""
Virtual GPU Orchestrator for Project X
Treats all free GPU tiers as ONE massive distributed GPU
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class GPUProvider(Enum):
    """Available free GPU providers."""
    GOOGLE_COLAB = "google_colab"
    KAGGLE = "kaggle"
    LIGHTNING_AI = "lightning_ai"
    SATURN_CLOUD = "saturn_cloud"
    PAPERSPACE = "paperspace"
    INTEL_TIBER = "intel_tiber"
    SAGEMAKER_STUDIO = "sagemaker_studio"
    GOOGLE_CLOUD_CREDITS = "google_cloud_credits"
    AZURE_CREDITS = "azure_credits"
    ORACLE_ALWAYS_FREE = "oracle_always_free"
    MODAL = "modal"


@dataclass
class GPUResource:
    """Represents a single GPU resource slot."""
    provider: GPUProvider
    gpu_type: str
    vram_gb: int
    weekly_hours: float
    max_session_hours: float
    requires_card: bool
    status: str = "available"
    current_session_start: Optional[datetime] = None
    total_used_hours_this_week: float = 0.0
    priority: int = 1


@dataclass
class ExperimentTask:
    """A task to be executed on GPU."""
    task_id: str
    name: str
    estimated_hours: float
    vram_required_gb: int
    priority: int = 1
    status: str = "pending"
    assigned_provider: Optional[GPUProvider] = None
    result: Optional[Dict] = None


class VirtualGPUCluster:
    """
    Virtual GPU Cluster
    Treats ALL free GPU providers as ONE massive GPU cluster.
    """

    def __init__(self):
        self.resources: List[GPUResource] = []
        self.tasks: List[ExperimentTask] = []
        self._init_resources()

    def _init_resources(self):
        """Initialize all free GPU resources."""

        # Tier 1: No card required, always free
        self.resources.extend([
            GPUResource(
                provider=GPUProvider.GOOGLE_COLAB,
                gpu_type="NVIDIA T4",
                vram_gb=16,
                weekly_hours=25,
                max_session_hours=12,
                requires_card=False,
                priority=10,
            ),
            GPUResource(
                provider=GPUProvider.KAGGLE,
                gpu_type="NVIDIA P100",
                vram_gb=16,
                weekly_hours=30,
                max_session_hours=12,
                requires_card=False,
                priority=9,
            ),
            GPUResource(
                provider=GPUProvider.KAGGLE,
                gpu_type="NVIDIA T4x2",
                vram_gb=32,
                weekly_hours=15,
                max_session_hours=12,
                requires_card=False,
                priority=8,
            ),
            GPUResource(
                provider=GPUProvider.LIGHTNING_AI,
                gpu_type="NVIDIA T4",
                vram_gb=16,
                weekly_hours=80,
                max_session_hours=4,
                requires_card=False,
                priority=7,
            ),
            GPUResource(
                provider=GPUProvider.SATURN_CLOUD,
                gpu_type="NVIDIA T4",
                vram_gb=16,
                weekly_hours=35,
                max_session_hours=8,
                requires_card=False,
                priority=6,
            ),
            GPUResource(
                provider=GPUProvider.PAPERSPACE,
                gpu_type="NVIDIA M4000",
                vram_gb=8,
                weekly_hours=20,
                max_session_hours=6,
                requires_card=False,
                priority=5,
            ),
            GPUResource(
                provider=GPUProvider.INTEL_TIBER,
                gpu_type="Intel Gaudi",
                vram_gb=48,
                weekly_hours=40,
                max_session_hours=8,
                requires_card=False,
                priority=4,
            ),
        ])

        # Tier 2: Credits (requires card but free)
        self.resources.extend([
            GPUResource(
                provider=GPUProvider.GOOGLE_CLOUD_CREDITS,
                gpu_type="NVIDIA T4",
                vram_gb=16,
                weekly_hours=100,
                max_session_hours=24,
                requires_card=True,
                priority=3,
            ),
            GPUResource(
                provider=GPUProvider.GOOGLE_CLOUD_CREDITS,
                gpu_type="NVIDIA A100",
                vram_gb=40,
                weekly_hours=35,
                max_session_hours=24,
                requires_card=True,
                priority=2,
            ),
            GPUResource(
                provider=GPUProvider.AZURE_CREDITS,
                gpu_type="NVIDIA V100",
                vram_gb=16,
                weekly_hours=50,
                max_session_hours=12,
                requires_card=True,
                priority=1,
            ),
            GPUResource(
                provider=GPUProvider.MODAL,
                gpu_type="NVIDIA T4",
                vram_gb=16,
                weekly_hours=50,
                max_session_hours=2,
                requires_card=False,
                priority=11,
            ),
        ])

    @property
    def total_weekly_hours(self) -> float:
        return sum(r.weekly_hours for r in self.resources)

    @property
    def total_vram_pool_gb(self) -> int:
        return sum(r.vram_gb for r in self.resources)

    def get_cluster_stats(self) -> Dict[str, Any]:
        return {
            "total_providers": len(set(r.provider for r in self.resources)),
            "total_gpu_slots": len(self.resources),
            "total_weekly_hours": self.total_weekly_hours,
            "total_vram_pool_gb": self.total_vram_pool_gb,
            "no_card_required_hours": sum(
                r.weekly_hours for r in self.resources if not r.requires_card
            ),
            "credit_required_hours": sum(
                r.weekly_hours for r in self.resources if r.requires_card
            ),
            "providers_breakdown": self._get_provider_breakdown(),
        }

    def _get_provider_breakdown(self) -> Dict[str, Dict]:
        breakdown = {}
        for r in self.resources:
            key = r.provider.value
            if key not in breakdown:
                breakdown[key] = {
                    "gpu_types": [],
                    "total_weekly_hours": 0,
                    "total_vram": 0,
                    "requires_card": r.requires_card,
                }
            breakdown[key]["gpu_types"].append(r.gpu_type)
            breakdown[key]["total_weekly_hours"] += r.weekly_hours
            breakdown[key]["total_vram"] += r.vram_gb
        return breakdown

    def schedule_task(self, task: ExperimentTask) -> bool:
        available = [
            r for r in self.resources 
            if r.status == "available" 
            and r.vram_gb >= task.vram_required_gb
            and r.weekly_hours - r.total_used_hours_this_week >= task.estimated_hours
        ]

        if not available:
            print("No GPU available for task: " + task.name)
            return False

        best = max(available, key=lambda r: r.priority)

        task.assigned_provider = best.provider
        task.status = "scheduled"
        best.status = "in_use"
        best.current_session_start = datetime.utcnow()

        print("Task scheduled: " + task.name + " on " + best.provider.value)
        return True

    def print_cluster_status(self):
        print("
" + "="*60)
        print("VIRTUAL GPU CLUSTER STATUS")
        print("="*60)
        print(f"{'Provider':<20} {'GPU':<15} {'VRAM':<8} {'Weekly':<8} {'Status':<10}")
        print("-"*60)

        for r in self.resources:
            remaining = r.weekly_hours - r.total_used_hours_this_week
            print(f"{r.provider.value:<20} {r.gpu_type:<15} {r.vram_gb}GB{'':<4} {r.weekly_hours:.0f}h{'':<3} {r.status:<10}")

        stats = self.get_cluster_stats()
        print("
SUMMARY:")
        print(f"  Total GPU Slots: {stats['total_gpu_slots']}")
        print(f"  Total Weekly Hours: {stats['total_weekly_hours']:.0f} hrs")
        print(f"  Total VRAM Pool: {stats['total_vram_pool_gb']} GB")
        print(f"  No-Card Hours: {stats['no_card_required_hours']:.0f} hrs")
        print(f"  Credit Hours: {stats['credit_required_hours']:.0f} hrs")


class ExperimentScheduler:
    """Intelligent Experiment Scheduler"""

    def __init__(self, cluster: VirtualGPUCluster):
        self.cluster = cluster
        self.task_queue: List[ExperimentTask] = []

    def submit_experiment(self, name: str, estimated_hours: float, vram_required_gb: int = 16, priority: int = 1) -> str:
        import uuid
        task_id = str(uuid.uuid4())[:8]

        task = ExperimentTask(
            task_id=task_id,
            name=name,
            estimated_hours=estimated_hours,
            vram_required_gb=vram_required_gb,
            priority=priority,
        )

        self.task_queue.append(task)
        print("Task submitted: " + name + " (ID: " + task_id + ")")
        return task_id

    def run_scheduler(self):
        print("
Starting Virtual GPU Scheduler...")

        self.task_queue.sort(key=lambda t: t.priority, reverse=True)

        scheduled = []
        failed = []

        for task in self.task_queue:
            if self.cluster.schedule_task(task):
                scheduled.append(task)
            else:
                failed.append(task)

        print("
Scheduled: " + str(len(scheduled)) + " tasks")
        if failed:
            print("Failed: " + str(len(failed)) + " tasks")
            for t in failed:
                print("  - " + t.name + " (needs " + str(t.vram_required_gb) + "GB, " + str(t.estimated_hours) + "h)")

        self.cluster.print_cluster_status()


# Test
if __name__ == "__main__":
    cluster = VirtualGPUCluster()
    scheduler = ExperimentScheduler(cluster)

    print("="*60)
    print("PROJECT X - VIRTUAL GPU CLUSTER")
    print("="*60)

    stats = cluster.get_cluster_stats()
    print("
CLUSTER STATISTICS:")
    print("  Total GPU Providers: " + str(stats['total_providers']))
    print("  Total GPU Slots: " + str(stats['total_gpu_slots']))
    print("  Total Weekly Hours: " + str(int(stats['total_weekly_hours'])) + " hours")
    print("  Total VRAM Pool: " + str(stats['total_vram_pool_gb']) + " GB")
    print("
COST BREAKDOWN:")
    print("  No Credit Card Required: " + str(int(stats['no_card_required_hours'])) + " hours/week")
    print("  Credits Required: " + str(int(stats['credit_required_hours'])) + " hours/week")

    print("
PROVIDER BREAKDOWN:")
    for provider, data in stats['providers_breakdown'].items():
        print("
  " + provider.upper() + ":")
        print("    GPUs: " + ", ".join(set(data['gpu_types'])))
        print("    Weekly Hours: " + str(int(data['total_weekly_hours'])))
        print("    Total VRAM: " + str(data['total_vram']) + " GB")
        print("    Requires Card: " + ("Yes" if data['requires_card'] else "No"))

    # Submit experiments
    scheduler.submit_experiment("bitcoin_key_analysis_100k", 4, 16, 10)
    scheduler.submit_experiment("feature_extraction_large", 8, 32, 8)
    scheduler.submit_experiment("cross_range_validation", 2, 8, 5)
    scheduler.submit_experiment("ml_baseline_test", 3, 16, 7)

    print("
" + "="*60)
    scheduler.run_scheduler()
