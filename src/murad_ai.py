\"\"\"
Murad AI Agent - Autonomous Experimentation AI
Uses AI Bridge to directly control GPU experiments
\"\"\"

import json
import time
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from rich.console import Console
from rich.panel import Panel

console = Console()


@dataclass
class ExperimentPlan:
    \"\"\"Plan for an experiment.\"\"\"
    name: str
    hypothesis: str
    parameters: Dict[str, Any]
    expected_outcome: str
    priority: int = 1


class MuradAI:
    \"\"\"
    Murad AI Agent

    Autonomous AI that:
    1. Generates experiment hypotheses
    2. Plans experiments
    3. Executes via AI Bridge
    4. Analyzes results
    5. Iterates and improves
    \"\"\"

    def __init__(self):
        self.experiments_run: List[Dict[str, Any]] = []
        self.learnings: List[str] = []
        self.current_focus = "bitcoin_key_locality"

        # Import bridge
        from .ai_bridge import get_bridge
        self.bridge = get_bridge()

        print("Murad AI Agent initialized")
        print(f"   Focus: {self.current_focus}")
        print("   Status: Ready for autonomous experimentation")

    def connect(self) -> bool:
        \"\"\"Connect to GPU system.\"\"\"
        return self.bridge.connect()

    def generate_hypothesis(self, based_on: Optional[Dict[str, Any]] = None) -> ExperimentPlan:
        \"\"\"Generate a new experiment hypothesis.\"\"\"

        if based_on:
            # Generate based on previous results
            prev_result = based_on.get("result", {})

            if "locality_score" in prev_result:
                # Previous experiment found locality - investigate further
                return ExperimentPlan(
                    name=f"locality_deep_dive_{int(time.time())}",
                    hypothesis="Increasing sample size will reveal clearer locality patterns",
                    parameters={
                        "sample_size": prev_result.get("sample_size", 10000) * 10,
                        "feature_dims": 48,  # More features
                    },
                    expected_outcome="Higher locality score with larger samples",
                    priority=2,
                )

        # Default: Bitcoin key analysis
        hypotheses = [
            ExperimentPlan(
                name=f"bitcoin_msb_analysis_{int(time.time())}",
                hypothesis="MSB (first byte) correlates strongly with key magnitude",
                parameters={
                    "sample_size": 100000,
                    "analysis_type": "msb_correlation",
                },
                expected_outcome="R^2 > 0.7 between MSB and log2(k)",
            ),
            ExperimentPlan(
                name=f"bitcoin_cross_range_{int(time.time())}",
                hypothesis="Locality does not generalize across magnitude ranges",
                parameters={
                    "sample_size": 50000,
                    "analysis_type": "cross_range",
                    "ranges": [(0, 2**64), (2**128, 2**192), (2**192, 2**256)],
                },
                expected_outcome="Poor cross-range generalization",
            ),
            ExperimentPlan(
                name=f"bitcoin_entropy_test_{int(time.time())}",
                hypothesis="Entropy patterns reveal key structure",
                parameters={
                    "sample_size": 200000,
                    "analysis_type": "entropy",
                },
                expected_outcome="Entropy clusters around specific values",
            ),
        ]

        return random.choice(hypotheses)

    def run_autonomous_experiment(self, max_iterations: int = 5) -> List[Dict[str, Any]]:
        \"\"\"Run autonomous experiment loop.\"\"\"
        results = []

        console.print(Panel.fit(
            "[bold cyan]Murad AI Starting Autonomous Experimentation[/bold cyan]\n"
            f"Max iterations: {max_iterations}",
            title="Murad AI",
            border_style="cyan"
        ))

        for i in range(max_iterations):
            console.print(f"\n[bold]Iteration {i+1}/{max_iterations}[/bold]")

            # 1. Generate hypothesis
            plan = self.generate_hypothesis(
                based_on=results[-1] if results else None
            )

            console.print(f"   Hypothesis: {plan.hypothesis}")
            console.print(f"   Parameters: {plan.parameters}")

            # 2. Execute via bridge
            response = self.bridge.execute(
                "run_experiment",
                name=plan.name,
                experiment_type="bitcoin",
                **plan.parameters
            )

            # 3. Analyze result
            result = {
                "iteration": i + 1,
                "plan": {
                    "name": plan.name,
                    "hypothesis": plan.hypothesis,
                    "parameters": plan.parameters,
                },
                "result": response.result,
                "status": response.status,
                "gpu": response.gpu_used,
                "time": response.execution_time,
            }

            results.append(result)
            self.experiments_run.append(result)

            # 4. Learn from result
            learning = self._analyze_result(plan, response)
            self.learnings.append(learning)

            console.print(f"   Learning: {learning}")

            # 5. Brief pause between iterations
            if i < max_iterations - 1:
                time.sleep(1)

        # Summary
        console.print(Panel.fit(
            f"[bold green]Autonomous Experimentation Complete[/bold green]\n"
            f"Total experiments: {len(results)}\n"
            f"Successful: {sum(1 for r in results if r['status'] == 'success')}\n"
            f"Learnings: {len(self.learnings)}",
            title="Murad AI Summary",
            border_style="green"
        ))

        return results

    def _analyze_result(self, plan: ExperimentPlan, response) -> str:
        \"\"\"Analyze experiment result and generate learning.\"\"\"
        if response.status != "success":
            return f"Experiment {plan.name} failed: {response.result.get('error', 'Unknown error')}"

        result = response.result

        if "locality_score" in result:
            score = result["locality_score"]
            if score > 0.5:
                return f"Strong locality detected (score={score:.3f}) - needs further investigation"
            else:
                return f"Weak locality (score={score:.3f}) - hypothesis may be incorrect"

        if "mean_feature_0" in result:
            return f"Feature analysis complete - mean={result['mean_feature_0']:.3f}"

        return f"Experiment {plan.name} completed successfully"

    def get_report(self) -> Dict[str, Any]:
        \"\"\"Generate experiment report.\"\"\"
        return {
            "total_experiments": len(self.experiments_run),
            "successful": sum(1 for r in self.experiments_run if r["status"] == "success"),
            "failed": sum(1 for r in self.experiments_run if r["status"] == "failed"),
            "learnings": self.learnings,
            "experiments": self.experiments_run,
        }

    def export_report(self, filepath: str) -> None:
        \"\"\"Export report to JSON.\"\"\"
        report = self.get_report()
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)
        console.print(f"Report exported to: {filepath}")


# Singleton
_ai_instance = None

def get_murad_ai() -> MuradAI:
    \"\"\"Get or create Murad AI instance.\"\"\"
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = MuradAI()
    return _ai_instance
