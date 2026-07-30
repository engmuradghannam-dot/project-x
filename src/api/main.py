"""
🌐 FastAPI Application - Project X
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from ..core.config import Config
from ..core.logger import get_logger, configure_logging
from .routers import experiments, health, metrics

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Project X API",
    description="🔬 Advanced Experimentation Framework API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["Experiments"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])


@app.on_event("startup")
async def startup_event():
    """Application startup."""
    logger.info("🚀 Project X API starting up...")
    config = Config()
    logger.info(f"Environment: {config.environment}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown."""
    logger.info("🛑 Project X API shutting down...")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Project X",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
