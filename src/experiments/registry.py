"""
📋 Experiment Registry - Register all experiments here
"""

from typing import Dict, Callable, List, Any
from functools import wraps


class ExperimentRegistry:
    """Registry for all experiments."""

    _experiments: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, description: str = "", tags: List[str] = None):
        """Decorator to register an experiment."""
        def decorator(func: Callable) -> Callable:
            cls._experiments[name] = {
                "function": func,
                "description": description,
                "tags": tags or [],
            }
            return func
        return decorator

    @classmethod
    def get_all(cls) -> Dict[str, Callable]:
        """Get all experiment functions."""
        return {name: data["function"] for name, data in cls._experiments.items()}

    @classmethod
    def get_by_tag(cls, tag: str) -> List[str]:
        """Get experiments by tag."""
        return [
            name for name, data in cls._experiments.items()
            if tag in data.get("tags", [])
        ]

    @classmethod
    def get_metadata(cls) -> Dict[str, Dict[str, Any]]:
        """Get metadata for all experiments."""
        return {
            name: {
                "description": data["description"],
                "tags": data["tags"],
            }
            for name, data in cls._experiments.items()
        }


# ═══════════════════════════════════════════════════
# 🧪 EXAMPLE EXPERIMENTS (Replace with your own!)
# ═══════════════════════════════════════════════════

@ExperimentRegistry.register(
    name="hello_world",
    description="Simple hello world experiment",
    tags=["example", "quick"]
)
def hello_world_experiment(name: str = "World") -> Dict[str, Any]:
    """Hello world experiment."""
    return {
        "message": f"Hello, {name}!",
        "experiment_type": "demo",
        "success": True,
    }


@ExperimentRegistry.register(
    name="math_test",
    description="Mathematical operations test",
    tags=["example", "math"]
)
def math_test_experiment(iterations: int = 1000) -> Dict[str, Any]:
    """Math test experiment."""
    import random
    import math

    results = []
    for _ in range(iterations):
        x = random.random()
        results.append(math.sin(x) + math.cos(x))

    return {
        "iterations": iterations,
        "mean": sum(results) / len(results),
        "min": min(results),
        "max": max(results),
    }


@ExperimentRegistry.register(
    name="data_processing",
    description="Sample data processing pipeline",
    tags=["example", "data", "nightly"]
)
def data_processing_experiment(rows: int = 10000) -> Dict[str, Any]:
    """Data processing experiment."""
    import pandas as pd
    import numpy as np

    # Generate sample data
    df = pd.DataFrame({
        'A': np.random.randn(rows),
        'B': np.random.randn(rows),
        'C': np.random.choice(['X', 'Y', 'Z'], rows),
    })

    # Process data
    result = df.groupby('C').agg({
        'A': ['mean', 'std'],
        'B': ['mean', 'std'],
    })

    return {
        "rows_processed": rows,
        "groups": len(result),
        "memory_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
    }


@ExperimentRegistry.register(
    name="ml_baseline",
    description="Machine learning baseline experiment",
    tags=["example", "ml", "nightly"]
)
def ml_baseline_experiment(n_samples: int = 1000, n_features: int = 20) -> Dict[str, Any]:
    """ML baseline experiment."""
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score

    # Generate data
    X, y = make_classification(n_samples=n_samples, n_features=n_features, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    return {
        "n_samples": n_samples,
        "n_features": n_features,
        "accuracy": accuracy,
        "n_estimators": 100,
    }
