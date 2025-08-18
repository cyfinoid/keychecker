#!/bin/bash

# Test script for KeyChecker
# This script runs all tests and quality checks

set -e

echo "🧪 Running KeyChecker tests and quality checks..."

# Install development dependencies if not already installed
echo "📦 Installing development dependencies..."
pip install -e ".[dev]"

# Run tests
echo "🔬 Running tests..."
pytest -v --cov=keychecker --cov-report=term-missing

# Run linting
echo "🔍 Running linting..."
flake8 keychecker/ tests/

# Run code formatting check
echo "🎨 Checking code formatting..."
black --check keychecker/ tests/

# Run type checking
echo "🔍 Running type checking..."
mypy keychecker/

# Run security checks (if bandit is available)
if command -v bandit &> /dev/null; then
    echo "🔒 Running security checks..."
    bandit -r keychecker/
else
    echo "⚠️  Bandit not installed, skipping security checks"
    echo "   Install with: pip install bandit"
fi

echo "✅ All tests and checks passed!"
