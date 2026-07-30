# ═══════════════════════════════════════════════════
# 🔥 Project X - Multi-Stage Docker Build
# ═══════════════════════════════════════════════════

# ─── Stage 1: Builder ─────────────────────────────
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     gcc     g++     && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --user -e ".[all]"

# ─── Stage 2: Production ──────────────────────────
FROM python:3.11-slim as production

LABEL maintainer="Murad Ghannam <eng.murad.ghannam@gmail.com>"
LABEL version="0.1.0"
LABEL description="Project X - Advanced Experimentation Framework"

WORKDIR /app

# Create non-root user
RUN groupadd -r projectx && useradd -r -g projectx projectx

# Copy installed packages from builder
COPY --from=builder /root/.local /home/projectx/.local
ENV PATH=/home/projectx/.local/bin:$PATH

# Copy application code
COPY --chown=projectx:projectx src/ ./src/
COPY --chown=projectx:projectx config/ ./config/
COPY --chown=projectx:projectx scripts/ ./scripts/

# Set permissions
RUN chmod +x scripts/*.sh

# Switch to non-root user
USER projectx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3     CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ─── Stage 3: Development ─────────────────────────
FROM production as development

USER root

# Install dev dependencies
RUN pip install --no-cache-dir -e ".[dev,test]"

# Install additional tools
RUN apt-get update && apt-get install -y --no-install-recommends     git     vim     curl     htop     && rm -rf /var/lib/apt/lists/*

USER projectx

# Default command for development
CMD ["bash"]

# ─── Stage 4: Experiment ────────────────────────────
FROM production as experiment

USER root

# Install experiment dependencies
RUN pip install --no-cache-dir -e ".[experiment]"

# Install Jupyter
RUN pip install --no-cache-dir jupyter jupyterlab

# Install system dependencies for experiments
RUN apt-get update && apt-get install -y --no-install-recommends     libgomp1     libblas-dev     liblapack-dev     && rm -rf /var/lib/apt/lists/*

USER projectx

# Jupyter port
EXPOSE 8888

# Default command for experiments
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
