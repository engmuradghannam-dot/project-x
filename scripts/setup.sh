#!/bin/bash
# Setup script for Project X

echo "Setting up Project X..."

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e ".[all]"

# Install pre-commit hooks
pre-commit install

echo "Setup complete! Activate with: source .venv/bin/activate"
