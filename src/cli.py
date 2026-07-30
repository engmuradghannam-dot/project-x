"""
⌨️ Project X - CLI Entry Point
"""

import typer
from rich.console import Console
from rich.panel import Panel

from .experiments.runner import ExperimentRunner
from .core.config import Config
from .core.logger import get_logger

app = typer.Typer(
    name="project-x",
    help="Project X - Advanced Experimentation Framework",
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
    """Run experiments."""
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
    from .api.main import app as fastapi_app

    console.print(f"Starting server on [bold]{host}:{port}[/bold]")
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
