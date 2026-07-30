#!/usr/bin/env python3
\"\"\"
Project X - Main Integration
Connects Kimi AI + Murad AI + GPU System
\"\"\"

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ai_bridge import get_bridge
from src.murad_ai import get_murad_ai


def main():
    print("=" * 70)
    print("PROJECT X - AI + GPU INTEGRATION")
    print("=" * 70)

    # 1. Connect AI Bridge
    print("\n[1] Connecting AI Bridge...")
    bridge = get_bridge()
    bridge.connect()

    # 2. Initialize Murad AI
    print("\n[2] Initializing Murad AI Agent...")
    murad = get_murad_ai()
    murad.connect()

    # 3. Show available GPUs
    print("\n[3] Detecting GPUs...")
    response = bridge.execute("detect_gpus")
    for name, info in response.result.items():
        status = "OK" if info["available"] else "XX"
        free = " [FREE]" if info["is_free"] else f" [${info['price']}/hr]"
        print(f"   {status} {name}: {info['vram_gb']}GB{free}")

    # 4. Run benchmark
    print("\n[4] Benchmarking...")
    response = bridge.execute("benchmark")
    if "error" not in response.result:
        print(f"   MatMul: {response.result.get('matmul_4096_time', 'N/A'):.3f}s")
        print(f"   FFT: {response.result.get('fft_16m_time', 'N/A'):.3f}s")

    # 5. Run autonomous experiments
    print("\n[5] Running Murad AI Autonomous Experiments...")
    results = murad.run_autonomous_experiment(max_iterations=3)

    # 6. Export report
    print("\n[6] Exporting report...")
    murad.export_report("murad_ai_report.json")

    print("\n" + "=" * 70)
    print("INTEGRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
