#!/bin/bash
# Run all tests

echo "Running Project X tests..."

# Unit tests
pytest tests/unit/ -v --cov=src --cov-report=html

# Integration tests
pytest tests/integration/ -v --cov=src --cov-append

# Coverage report
coverage report

echo "Tests complete!"
