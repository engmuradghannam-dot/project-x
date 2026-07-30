"""
🔬 Experiments API Router
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

from ...core.engine import ExperimentEngine
from ...core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
engine = ExperimentEngine()


class ExperimentRequest(BaseModel):
    name: str
    parameters: Optional[Dict[str, Any]] = {}


class ExperimentResponse(BaseModel):
    experiment_id: str
    name: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    metrics: Dict[str, Any] = {}
    duration_seconds: float = 0.0


@router.get("/", response_model=List[ExperimentResponse])
async def list_experiments():
    """List all experiments."""
    results = engine.get_results()
    return [ExperimentResponse(**r.to_dict()) for r in results]


@router.post("/run", response_model=ExperimentResponse)
async def run_experiment(request: ExperimentRequest, background_tasks: BackgroundTasks):
    """Run an experiment."""
    if request.name not in engine.experiments:
        raise HTTPException(status_code=404, detail=f"Experiment '{request.name}' not found")

    result = engine.run(request.name, **request.parameters)
    return ExperimentResponse(**result.to_dict())


@router.get("/summary")
async def get_summary():
    """Get experiment summary."""
    return engine.get_summary()


@router.get("/{experiment_id}")
async def get_experiment(experiment_id: str):
    """Get experiment by ID."""
    for result in engine.results:
        if result.experiment_id == experiment_id:
            return result.to_dict()
    raise HTTPException(status_code=404, detail="Experiment not found")
