"""
🔥 Experiment Engine - The Heart of Project X
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
import uuid

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .logger import get_logger
from .config import Config

console = Console()
logger = get_logger(__name__)


@dataclass
class ExperimentResult:
    """Result of a single experiment run."""
    experiment_id: str
    name: str
    status: str  # 'success', 'failed', 'running'
    start_time: datetime
    end_time: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def duration_seconds(self) -> float:
        """Calculate experiment duration."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "metrics": self.metrics,
            "artifacts": self.artifacts,
            "error": self.error,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class ExperimentEngine:
    """
    🔥 Main Experiment Engine

    Manages experiment lifecycle:
    - Registration
    - Execution
    - Monitoring
    - Reporting
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.experiments: Dict[str, Callable] = {}
        self.results: List[ExperimentResult] = []
        self._running: Dict[str, ExperimentResult] = {}
        logger.info("🚀 Experiment Engine initialized")

    def register(self, name: str, experiment_func: Callable) -> None:
        """Register an experiment function."""
        self.experiments[name] = experiment_func
        logger.info(f"📋 Registered experiment: {name}")

    def run(self, name: str, **kwargs) -> ExperimentResult:
        """Run a single experiment."""
        if name not in self.experiments:
            raise ValueError(f"Experiment '{name}' not registered")

        experiment_id = str(uuid.uuid4())[:8]
        result = ExperimentResult(
            experiment_id=experiment_id,
            name=name,
            status="running",
            start_time=datetime.utcnow(),
        )
        self._running[experiment_id] = result

        console.print(f"\n🔬 [bold cyan]Running Experiment: {name}[/bold cyan] (ID: {experiment_id})")

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Executing {name}...", total=None)

                # Run the experiment
                metrics = self.experiments[name](**kwargs)

                progress.update(task, completed=True)

            result.status = "success"
            result.metrics = metrics if isinstance(metrics, dict) else {"output": metrics}
            logger.info(f"✅ Experiment {name} completed successfully")

        except Exception as e:
            result.status = "failed"
            result.error = str(e)
            logger.error(f"❌ Experiment {name} failed: {e}")

        finally:
            result.end_time = datetime.utcnow()
            del self._running[experiment_id]
            self.results.append(result)

        # Print summary
        self._print_result(result)
        return result

    def run_all(self) -> List[ExperimentResult]:
        """Run all registered experiments."""
        console.print(f"\n🔥 [bold green]Running {len(self.experiments)} Experiments[/bold green]\n")
        results = []
        for name in self.experiments:
            result = self.run(name)
            results.append(result)
        return results

    def get_results(self, status: Optional[str] = None) -> List[ExperimentResult]:
        """Get experiment results, optionally filtered by status."""
        if status:
            return [r for r in self.results if r.status == status]
        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all experiments."""
        total = len(self.results)
        success = len([r for r in self.results if r.status == "success"])
        failed = len([r for r in self.results if r.status == "failed"])
        total_duration = sum(r.duration_seconds for r in self.results)

        return {
            "total_experiments": total,
            "successful": success,
            "failed": failed,
            "success_rate": success / total * 100 if total > 0 else 0,
            "total_duration_seconds": total_duration,
            "average_duration_seconds": total_duration / total if total > 0 else 0,
        }

    def export_results(self, filepath: str) -> None:
        """Export all results to JSON file."""
        data = {
            "summary": self.get_summary(),
            "results": [r.to_dict() for r in self.results],
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"📊 Results exported to {filepath}")

    def _print_result(self, result: ExperimentResult) -> None:
        """Print experiment result to console."""
        status_color = {
            "success": "green",
            "failed": "red",
            "running": "yellow",
        }.get(result.status, "white")

        console.print(f"\n{'─' * 60}")
        console.print(f"📊 [bold]Experiment:[/bold] {result.name}")
        console.print(f"🆔 [bold]ID:[/bold] {result.experiment_id}")
        console.print(f"📈 [bold]Status:[/bold] [{status_color}]{result.status}[/{status_color}]")
        console.print(f"⏱️  [bold]Duration:[/bold] {result.duration_seconds:.2f}s")

        if result.metrics:
            console.print(f"\n📈 [bold]Metrics:[/bold]")
            for key, value in result.metrics.items():
                console.print(f"   • {key}: {value}")

        if result.error:
            console.print(f"\n❌ [bold red]Error:[/bold red] {result.error}")

        console.print(f"{'─' * 60}\n")
