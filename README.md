# Project X - Advanced Experimentation Framework

[![CI/CD](https://github.com/engmuradghannam-dot/project-x/actions/workflows/ci.yml/badge.svg)](https://github.com/engmuradghannam-dot/project-x/actions/workflows/ci.yml)
[![Security](https://github.com/engmuradghannam-dot/project-x/actions/workflows/security.yml/badge.svg)](https://github.com/engmuradghannam-dot/project-x/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/engmuradghannam-dot/project-x/branch/main/graph/badge.svg)](https://codecov.io/gh/engmuradghannam-dot/project-x)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Overview

Project X is a production-ready experimentation framework designed for running, monitoring, and analyzing experiments at scale. Built with modern Python tooling and complete CI/CD automation.

## Features

- **Experiment Engine**: Register and run experiments with full lifecycle management
- **REST API**: FastAPI-based API for remote experiment control
- **CLI Tool**: Command-line interface for local experiment execution
- **Full CI/CD**: 7 GitHub Actions workflows covering all aspects
- **Security Scanning**: CodeQL, Trivy, Bandit, Safety, TruffleHog
- **Docker Support**: Multi-stage builds for production, dev, and experiments
- **Monitoring**: Prometheus metrics + Grafana dashboards
- **Auto-Release**: Automated versioning and publishing

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/engmuradghannam-dot/project-x.git
cd project-x

# Install dependencies
pip install -e ".[all]"

# Or with Docker
docker-compose up -d
```

### Running Experiments

```bash
# List all experiments
project-x list

# Run a specific experiment
project-x run --name hello_world

# Run all experiments
project-x run --all

# Run nightly suite
project-x run --nightly
```

### Starting the API

```bash
# Start the API server
project-x serve

# Or with auto-reload (development)
project-x serve --reload
```

### Using Docker

```bash
# Production
docker-compose up api

# With experiments
docker-compose --profile experiment up experiment

# With monitoring
docker-compose --profile monitoring up
```

## Project Structure

```
project-x/
├── .github/
│   ├── workflows/          # GitHub Actions workflows
│   │   ├── ci.yml          # Main CI/CD pipeline
│   │   ├── release.yml     # Release automation
│   │   ├── security.yml    # Security scanning
│   │   ├── nightly.yml     # Nightly experiments
│   │   ├── dependabot.yml  # Auto-merge Dependabot PRs
│   │   ├── auto-push.yml   # Auto-sync to mirrors
│   │   └── cleanup.yml     # Cleanup old artifacts
│   ├── dependabot.yml      # Dependabot configuration
│   └── CODEOWNERS          # Code ownership
├── src/
│   ├── core/               # Core engine, config, logging
│   ├── api/                # FastAPI application
│   ├── experiments/        # Experiment registry & runner
│   ├── plugins/            # Plugin system
│   └── cli.py              # CLI entry point
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/                # End-to-end tests
├── docker/
│   ├── Dockerfile          # Multi-stage Docker build
│   └── docker-compose.yml  # Docker Compose config
├── config/                 # Configuration files
├── scripts/                # Utility scripts
├── docs/                   # Documentation
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **CI/CD** | Push/PR | Full pipeline: lint, test, build, deploy |
| **Security** | Push/PR/Schedule | CodeQL, Trivy, Bandit, Safety, TruffleHog |
| **Release** | Tag push | Changelog, GitHub release, PyPI publish |
| **Nightly** | Daily 2 AM | Experiments + benchmarks |
| **Dependabot** | Dependabot PR | Auto-merge minor/patch updates |
| **Auto-Push** | CI success | Sync to GitLab/Bitbucket mirrors |
| **Cleanup** | Weekly | Delete old artifacts and runs |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Project info |
| `/health/` | GET | Health check |
| `/health/ready` | GET | Readiness check |
| `/health/live` | GET | Liveness check |
| `/api/v1/experiments/` | GET | List experiments |
| `/api/v1/experiments/run` | POST | Run experiment |
| `/api/v1/experiments/summary` | GET | Experiment summary |
| `/metrics` | GET | Prometheus metrics |

## Writing Experiments

```python
from src.experiments.registry import ExperimentRegistry

@ExperimentRegistry.register(
    name="my_experiment",
    description="My custom experiment",
    tags=["custom", "ml"]
)
def my_experiment(param1: int = 100) -> dict:
    # Your experiment logic here
    return {
        "param1": param1,
        "result": "success",
    }
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | App environment |
| `DATABASE_URL` | PostgreSQL URL | Database connection |
| `REDIS_URL` | Redis URL | Redis connection |
| `API_HOST` | `0.0.0.0` | API host |
| `API_PORT` | `8000` | API port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `SECRET_KEY` | - | Secret key for production |

## License

MIT License - See [LICENSE](LICENSE) for details.

---

Built with by Murad Ghannam
