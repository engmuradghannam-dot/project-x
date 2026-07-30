#!/usr/bin/env python3
\"\"\"
GPU Status Monitor - Shows GPU is always connected and working
\"\"\"

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.gpu_connector import check_gpu_status, get_gpu, get_runner, get_bridge
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout

console = Console()


def show_gpu_status():
    \"\"\"Display current GPU status.\"\"\"
    status = check_gpu_status()

    if status["connected"]:
        table = Table(title="GPU Status - CONNECTED", style="green")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Status", "ONLINE")
        table.add_row("GPU Name", status["gpu_name"])
        table.add_row("VRAM Total", f"{status['vram_total_gb']:.1f} GB")
        table.add_row("VRAM Used", f"{status['vram_used_gb']:.1f} GB")
        table.add_row("VRAM Free", f"{status['vram_free_gb']:.1f} GB")
        table.add_row("Utilization", f"{status['utilization']:.1f}%")

        console.print(table)
    else:
        console.print(Panel(
            f"[red]GPU OFFLINE: {status['message']}[/red]",
            title="GPU Status",
            border_style="red"
        ))


def monitor_loop():
    \"\"\"Continuous monitoring loop.\"\"\"
    console.print("[bold green]GPU Monitor Started - Press Ctrl+C to stop[/bold green]")

    try:
        while True:
            console.clear()
            show_gpu_status()
            time.sleep(5)
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitor stopped[/yellow]")


def quick_check():
    \"\"\"Quick GPU check.\"\"\"
    status = check_gpu_status()

    if status["connected"]:
        console.print(f"[green]GPU OK[/green] | {status['gpu_name']} | {status['vram_free_gb']:.1f}GB free")
        return True
    else:
        console.print(f"[red]GPU ERROR[/red] | {status['message']}")
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--monitor", "-m", action="store_true", help="Continuous monitoring")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick check")
    args = parser.parse_args()

    if args.monitor:
        monitor_loop()
    elif args.quick:
        quick_check()
    else:
        show_gpu_status()
