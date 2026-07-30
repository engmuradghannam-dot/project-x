"""
E2E Tests for Project X
"""

import pytest
import requests
import time

# These tests assume the API is running
BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def api_url():
    """Get API URL."""
    return BASE_URL


class TestEndToEnd:
    """End-to-end tests."""

    def test_full_workflow(self, api_url):
        """Test full experiment workflow."""
        # 1. Check health
        response = requests.get(f"{api_url}/health/")
        assert response.status_code == 200

        # 2. List experiments
        response = requests.get(f"{api_url}/api/v1/experiments/")
        assert response.status_code == 200
        experiments = response.json()

        # 3. Run an experiment
        if experiments:
            exp_name = experiments[0]["name"]
            response = requests.post(
                f"{api_url}/api/v1/experiments/run",
                json={"name": exp_name, "parameters": {}}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"

        # 4. Get summary
        response = requests.get(f"{api_url}/api/v1/experiments/summary")
        assert response.status_code == 200


class TestPerformance:
    """Performance tests."""

    def test_api_response_time(self, api_url):
        """Test API response time."""
        start = time.time()
        response = requests.get(f"{api_url}/health/")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0  # Should respond in less than 1 second
