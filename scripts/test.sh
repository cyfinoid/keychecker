#!/bin/bash

# Test script for KeyChecker using uv
# This script runs all tests and quality checks using uv for faster execution

set -e

echo "🧪 Running KeyChecker tests and quality checks with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Please install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "Please run ./scripts/setup-dev-uv.sh first"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

echo "🔍 Running code formatting check..."
uv run black --check --diff . || {
    echo "❌ Code formatting issues found. Run 'uv run black .' to fix them."
    exit 1
}

echo "🔍 Running linting..."
uv run flake8 keychecker/ tests/ || {
    echo "❌ Linting issues found."
    exit 1
}

echo "🔍 Running type checking..."
uv run mypy keychecker/ || {
    echo "❌ Type checking issues found."
    exit 1
}

echo "🧪 Running tests with coverage..."
uv run pytest -v --cov=keychecker --cov-report=term-missing --cov-report=html tests/

echo "🔒 Running security checks..."
echo "Running bandit security scan..."
uv run bandit -r keychecker/ || echo "⚠️  Bandit found some security issues (check output above)"

echo "Running safety vulnerability check..."
uv run safety check || echo "⚠️  Safety found some vulnerabilities (check output above)"

echo ""
echo "✅ All tests and checks completed!"
echo ""
echo "📊 Coverage report generated in htmlcov/index.html"
echo "🔍 To view coverage report: open htmlcov/index.html"
