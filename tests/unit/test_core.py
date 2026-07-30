"""
Unit Tests for Project X Core
"""

import pytest
from datetime import datetime

from src.core.engine import ExperimentEngine, ExperimentResult
from src.core.config import Config


class TestExperimentResult:
    """Test ExperimentResult dataclass."""

    def test_duration_calculation(self):
        """Test duration calculation."""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 12, 0, 5)

        result = ExperimentResult(
            experiment_id="test-001",
            name="test",
            status="success",
            start_time=start,
            end_time=end,
        )

        assert result.duration_seconds == 5.0

    def test_to_dict(self):
        """Test conversion to dict."""
        result = ExperimentResult(
            experiment_id="test-001",
            name="test",
            status="success",
            start_time=datetime.utcnow(),
            metrics={"accuracy": 0.95},
        )

        d = result.to_dict()
        assert d["experiment_id"] == "test-001"
        assert d["metrics"]["accuracy"] == 0.95


class TestExperimentEngine:
    """Test ExperimentEngine."""

    def test_register_experiment(self):
        """Test experiment registration."""
        engine = ExperimentEngine()

        def dummy_exp():
            return {"result": "ok"}

        engine.register("dummy", dummy_exp)
        assert "dummy" in engine.experiments

    def test_run_experiment(self):
        """Test running an experiment."""
        engine = ExperimentEngine()

        def dummy_exp():
            return {"result": "ok"}

        engine.register("dummy", dummy_exp)
        result = engine.run("dummy")

        assert result.status == "success"
        assert result.metrics["result"] == "ok"

    def test_run_nonexistent_experiment(self):
        """Test running non-existent experiment."""
        engine = ExperimentEngine()

        with pytest.raises(ValueError):
            engine.run("nonexistent")

    def test_get_summary(self):
        """Test summary generation."""
        engine = ExperimentEngine()

        def success_exp():
            return {"result": "ok"}

        def fail_exp():
            raise ValueError("Test error")

        engine.register("success", success_exp)
        engine.register("fail", fail_exp)

        engine.run("success")
        try:
            engine.run("fail")
        except:
            pass

        summary = engine.get_summary()
        assert summary["total_experiments"] == 2
        assert summary["successful"] == 1
        assert summary["failed"] == 1


class TestConfig:
    """Test Config."""

    def test_default_values(self):
        """Test default configuration."""
        config = Config()
        assert config.app_name == "Project X"
        assert config.version == "0.1.0"

    def test_environment_check(self):
        """Test environment checks."""
        config = Config()
        config.environment = "production"
        assert config.is_production is True
        assert config.is_development is False
