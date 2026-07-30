"""
⌨️ Project X - CLI with GPU Support
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .experiments.runner import ExperimentRunner
from .core.config import Config
from .core.logger import get_logger
from .core.gpu_integration import GPUExperimentRunner, create_bitcoin_experiment
from .core.virtual_gpu import VirtualGPUCluster

app = typer.Typer(
    name="project-x",
    help="Project X - Advanced Experimentation Framework with Virtual GPU",
    rich_markup_mode="rich",
)
console = Console()
logger = get_logger(__name__)


@app.command()
def run(
    name: str = typer.Option(None, "--name", "-n", help="Experiment name to run"),
    all: bool = typer.Option(False, "--all", "-a", help="Run all experiments"),
    nightly: bool = typer.Option(False, "--nightly", help="Run nightly suite"),
    output_dir: str = typer.Option("./experiments-output", "--output-dir", "-o", help="Output directory"),
):
    """Run experiments locally."""
    runner = ExperimentRunner()

    if nightly:
        runner.run_nightly()
        runner.export_results(output_dir)
    elif all:
        runner.run()
        runner.export_results(output_dir)
    elif name:
        runner.run(name)
        runner.export_results(output_dir)
    else:
        console.print("[red]Please specify --name, --all, or --nightly[/red]")


@app.command()
def list():
    """List all experiments."""
    runner = ExperimentRunner()
    runner.list_experiments()


@app.command()
def info():
    """Show project information."""
    config = Config()

    panel = Panel.fit(
        f"""[bold cyan]Project X[/bold cyan]

[b]Version:[/b] {config.version}
[b]Environment:[/b] {config.environment}
[b]Debug:[/b] {config.debug}
[b]API:[/b] {config.api_host}:{config.api_port}

[dim]Ready for experiments![/dim]""",
        title="Project Information",
        border_style="green",
    )
    console.print(panel)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
):
    """Start the API server."""
    import uvicorn

    console.print(f"Starting server on [bold]{host}:{port}[/bold]")
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


# ═══════════════════════════════════════════════════
# 🖥️ GPU COMMANDS
# ═══════════════════════════════════════════════════

@app.command()
def gpu_status():
    """Show Virtual GPU Cluster status."""
    cluster = VirtualGPUCluster()
    cluster.print_cluster_status()


@app.command()
def gpu_providers():
    """List all available GPU providers."""
    runner = GPUExperimentRunner()
    providers = runner.list_providers()

    table = Table(title="Available GPU Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Description", style="green")

    for name, desc in providers.items():
        table.add_row(name, desc)

    console.print(table)


@app.command()
def gpu_run(
    name: str = typer.Option(..., "--name", "-n", help="Experiment name"),
    sample_size: int = typer.Option(10000, "--samples", "-s", help="Sample size"),
    vram: int = typer.Option(16, "--vram", "-v", help="VRAM required (GB)"),
    hours: float = typer.Option(2, "--hours", "-t", help="Estimated hours"),
):
    """Run an experiment on GPU cloud."""
    console.print(f"[bold cyan]🚀 Running '{name}' on Virtual GPU Cluster...[/bold cyan]
")

    runner = GPUExperimentRunner()
    config = create_bitcoin_experiment(sample_size)
    config.name = name
    config.estimated_hours = hours
    config.vram_required_gb = vram

    result = runner.run_experiment(config)

    if "error" in result:
        console.print(f"[red]❌ Error: {result['error']}[/red]")
    else:
        console.print(f"[green]✅ Experiment scheduled![/green]")
        console.print(f"  Task ID: {result['task_id']}")
        console.print(f"  Provider: {result['provider']}")
        console.print(f"  GPU: {result['gpu']} ({result['vram']}GB VRAM)")
        console.print(f"  Status: {result['status']}")


@app.command()
def gpu_batch(
    count: int = typer.Option(3, "--count", "-c", help="Number of experiments"),
    sample_size: int = typer.Option(10000, "--samples", "-s", help="Sample size"),
):
    """Run batch experiments on GPU cloud."""
    console.print(f"[bold cyan]🚀 Running {count} experiments on GPU Cluster...[/bold cyan]
")

    runner = GPUExperimentRunner()
    configs = []

    for i in range(count):
        config = create_bitcoin_experiment(sample_size)
        config.name = f"batch_experiment_{i+1}"
        config.priority = count - i  # Higher priority for first experiments
        configs.append(config)

    results = runner.run_batch(configs)

    table = Table(title="Batch Results")
    table.add_column("#", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Provider", style="yellow")
    table.add_column("GPU", style="magenta")
    table.add_column("Status", style="white")

    for i, result in enumerate(results):
        status = "✅" if "error" not in result else "❌"
        table.add_row(
            str(i+1),
            result.get("task_id", "N/A"),
            result.get("provider", "N/A"),
            result.get("gpu", "N/A"),
            f"{status} {result.get('status', 'unknown')}",
        )

    console.print(table)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
