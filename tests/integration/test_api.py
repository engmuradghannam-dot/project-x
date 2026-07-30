"""
Integration Tests for Project X API
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self):
        """Test basic health check."""
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_readiness_check(self):
        """Test readiness check."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_liveness_check(self):
        """Test liveness check."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Project X"
        assert "version" in data


class TestExperimentsAPI:
    """Test experiments API."""

    def test_list_experiments(self):
        """Test listing experiments."""
        response = client.get("/api/v1/experiments/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_experiment_summary(self):
        """Test experiment summary."""
        response = client.get("/api/v1/experiments/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_experiments" in data
