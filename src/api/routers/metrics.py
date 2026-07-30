"""
📊 Metrics Router
"""

from fastapi import APIRouter
from prometheus_client import Counter, Histogram, Gauge, generate_latest

router = APIRouter()

# Define metrics
REQUEST_COUNT = Counter(
    'project_x_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'project_x_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_EXPERIMENTS = Gauge(
    'project_x_active_experiments',
    'Number of active experiments'
)

EXPERIMENT_DURATION = Histogram(
    'project_x_experiment_duration_seconds',
    'Experiment duration in seconds',
    ['experiment_name']
)


@router.get("/prometheus")
async def get_prometheus_metrics():
    """Get Prometheus metrics."""
    return generate_latest()
