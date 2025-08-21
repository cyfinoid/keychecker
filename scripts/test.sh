#!/bin/bash

# Test script for KeyChecker
# This script runs all tests and quality checks using uv for fast execution

set -e

echo "🧪 Running KeyChecker tests and quality checks..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Please run ./scripts/install.sh first"
    exit 1
fi

# Function to activate virtual environment
activate_venv() {
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
    
    # Verify activation worked
    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo "❌ Error: Failed to activate virtual environment"
        exit 1
    fi
}

# Check virtual environment status
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "✅ Already in virtual environment: $VIRTUAL_ENV"
elif [[ -d ".venv" ]]; then
    echo "📦 Virtual environment exists, activating..."
    activate_venv
else
    echo "❌ Error: Virtual environment not found"
    echo "🔧 To fix this, run:"
    echo "   ./scripts/setup-dev.sh    # Set up development environment"
    exit 1
fi

# Double-check we're in a virtual environment before proceeding
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "❌ Error: Not in a virtual environment. This is required to avoid system package conflicts."
    echo "🔧 Please run: ./scripts/setup-dev.sh"
    exit 1
fi

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
uv run pytest -v tests/

echo "🔒 Running security checks..."
echo "Running bandit security scan..."
uv run bandit -r keychecker/ || echo "⚠️  Bandit found some security issues (check output above)"

echo "Running pip-audit vulnerability check..."
uv run pip-audit --skip-editable || echo "⚠️  pip-audit found some vulnerabilities (check output above)"
echo "Checking uv requirements for vulnerabilities..."
uv run pip-audit -r requirements-uv.txt || echo "⚠️  pip-audit found vulnerabilities in uv requirements"

echo ""
echo "✅ All tests and checks completed!"
echo ""
