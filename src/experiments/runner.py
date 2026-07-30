"""
🧪 Experiment Runner - Execute all experiments
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from ..core.engine import ExperimentEngine
from ..core.config import Config
from ..core.logger import get_logger
from .registry import ExperimentRegistry

console = Console()
logger = get_logger(__name__)


class ExperimentRunner:
    """Runner for all experiments."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.engine = ExperimentEngine(config)
        self.registry = ExperimentRegistry()
        self._register_all()

    def _register_all(self) -> None:
        """Register all experiments from registry."""
        for name, func in self.registry.get_all().items():
            self.engine.register(name, func)

    def run(self, name: Optional[str] = None, **kwargs) -> None:
        """Run experiment(s)."""
        if name:
            self.engine.run(name, **kwargs)
        else:
            self.engine.run_all()

    def run_nightly(self) -> None:
        """Run nightly experiment suite."""
        console.print("\n🌙 [bold blue]Nightly Experiment Suite[/bold blue]\n")
        nightly_experiments = self.registry.get_by_tag("nightly")
        for name in nightly_experiments:
            self.engine.run(name)

    def list_experiments(self) -> None:
        """List all available experiments."""
        table = Table(title="🔬 Available Experiments")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="green")
        table.add_column("Tags", style="yellow")

        for name, meta in self.registry.get_metadata().items():
            table.add_row(
                name,
                meta.get("description", "No description"),
                ", ".join(meta.get("tags", []))
            )

        console.print(table)

    def export_results(self, output_dir: Optional[str] = None) -> None:
        """Export results."""
        output_path = Path(output_dir or self.config.experiment_output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filepath = output_path / "experiment_results.json"
        self.engine.export_results(str(filepath))
        console.print(f"📊 Results exported to: {filepath}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="🔬 Project X - Experiment Runner")
    parser.add_argument("--all", action="store_true", help="Run all experiments")
    parser.add_argument("--nightly", action="store_true", help="Run nightly suite")
    parser.add_argument("--list", action="store_true", help="List experiments")
    parser.add_argument("--name", type=str, help="Run specific experiment")
    parser.add_argument("--output-dir", type=str, default="./experiments-output", help="Output directory")

    args = parser.parse_args()

    runner = ExperimentRunner()

    if args.list:
        runner.list_experiments()
    elif args.nightly:
        runner.run_nightly()
        runner.export_results(args.output_dir)
    elif args.all:
        runner.run()
        runner.export_results(args.output_dir)
    elif args.name:
        runner.run(args.name)
        runner.export_results(args.output_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
