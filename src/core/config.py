"""
⚙️ Configuration Management for Project X
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Project X Configuration."""

    # Application
    app_name: str = "Project X"
    version: str = "0.1.0"
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # Database
    database_url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/project_x"
    ))

    # Redis
    redis_url: str = field(default_factory=lambda: os.getenv(
        "REDIS_URL", "redis://localhost:6379/0"
    ))

    # API
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    api_workers: int = field(default_factory=lambda: int(os.getenv("API_WORKERS", "4")))

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_format: str = "json"

    # Experiments
    experiment_output_dir: str = field(default_factory=lambda: os.getenv("EXPERIMENT_OUTPUT_DIR", "./experiments-output"))
    max_experiment_duration: int = 3600  # seconds

    # Security
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "change-me-in-production"))

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excludes sensitive data)."""
        return {
            "app_name": self.app_name,
            "version": self.version,
            "environment": self.environment,
            "debug": self.debug,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "log_level": self.log_level,
            "experiment_output_dir": self.experiment_output_dir,
        }
