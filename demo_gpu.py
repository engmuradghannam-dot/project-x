#!/usr/bin/env python3
"""
🚀 Project X GPU Virtualization Demo
Shows how the system automatically finds and uses the best GPU
"""

import numpy as np
from src.gpu_virtualization import GPUManager, VirtualGPU, GPUBackend
from src.gpu_virtualization.experiment_runner import GPUExperimentRunner, bitcoin_key_analysis


def main():
    print("=" * 70)
    print("🔥 PROJECT X - GPU VIRTUALIZATION SYSTEM DEMO")
    print("=" * 70)

    # Step 1: Detect all available GPUs
    print("\n📡 STEP 1: Detecting GPU backends...")
    print("-" * 70)

    manager = GPUManager()
    statuses = manager.detect_all()

    # Step 2: Show GPU catalog
    print("\n📋 STEP 2: GPU Catalog")
    print("-" * 70)
    for backend, specs in [
        (GPUBackend.CPU_RAM, "💾 CPU-RAM (Free - Uses System RAM)"),
        (GPUBackend.COLAB_T4, "🔵 Google Colab T4 (Free - 16GB)"),
        (GPUBackend.KAGGLE_P100, "🟣 Kaggle P100 (Free - 16GB)"),
        (GPUBackend.VAST_AI, "🟢 Vast.ai H100 (Cheap - $2/hr - 80GB)"),
        (GPUBackend.RUNPOD, "🟠 RunPod H100 (Cheap - $2.49/hr - 80GB)"),
    ]:
        print(f"   {specs}")

    # Step 3: Initialize best free GPU
    print("\n🎯 STEP 3: Initializing Best Free GPU")
    print("-" * 70)

    gpu = manager.get_best_free()

    if gpu:
        print(f"\n✅ Active GPU: {gpu.specs.name}")
        print(f"   VRAM: {gpu.specs.vram_gb} GB")
        print(f"   Compute Units: {gpu.specs.compute_units}")
        print(f"   Price: ${gpu.specs.price_per_hour}/hr")

        # Step 4: Benchmark
        print("\n⚡ STEP 4: Running Benchmark")
        print("-" * 70)

        results = gpu.benchmark()
        print(f"\n   Matrix Multiply (4096x4096): {results['matmul_4096_time']:.3f}s")
        print(f"   FFT (16M elements): {results['fft_16m_time']:.3f}s")

        # Step 5: Run sample experiment
        print("\n🧪 STEP 5: Running Sample Experiment")
        print("-" * 70)

        runner = GPUExperimentRunner(force_gpu="cpu")

        # Simple matrix experiment
        def matrix_experiment(gpu, size=2048, **kwargs):
            a = np.random.randn(size, size).astype(np.float32)
            b = np.random.randn(size, size).astype(np.float32)
            result = gpu.matmul(a, b)
            return {"shape": result.shape, "mean": float(np.mean(result))}

        result = runner.run_experiment("matrix_test", matrix_experiment, size=2048)

        # Step 6: Show utilization
        print("\n📊 STEP 6: GPU Utilization")
        print("-" * 70)

        util = gpu.get_utilization()
        print(f"   Memory Used: {util['memory_used_gb']:.2f} / {util['memory_total_gb']:.2f} GB")
        print(f"   Memory Utilization: {util['memory_utilization']:.1f}%")

    # Step 7: Show cloud spawning capability
    print("\n☁️  STEP 7: Cloud GPU Options (On-Demand)")
    print("-" * 70)
    print("   Vast.ai H100: $2.00/hr (80GB VRAM)")
    print("   RunPod H100: $2.49/hr (80GB VRAM)")
    print("   AWS G4dn T4: $0.53/hr (16GB VRAM)")
    print("\n   💡 Use: runner.spawn_cloud_if_needed(min_vram_gb=32)")

    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)
    print("\n📝 Summary:")
    print("   • System auto-detects all GPU backends")
    print("   • Prioritizes FREE options (Colab, Kaggle, CPU-RAM)")
    print("   • Falls back to CPU-RAM virtualization")
    print("   • Can spawn cloud GPU on demand")
    print("   • Tracks cost and utilization automatically")
    print("\n🚀 Ready for Murad AI experiments!")


if __name__ == "__main__":
    main()
