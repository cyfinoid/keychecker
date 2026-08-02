#!/bin/bash

# Development setup script for KeyChecker
# This script sets up the development environment using uv for fast dependency management

set -e

echo "🚀 Setting up KeyChecker development environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo ""
    echo "📦 Installing uv..."
    echo "Please install uv first:"
    echo ""
    echo "  # Using curl (recommended, versioned to match requirements-uv.txt)"
    echo "  curl -LsSf https://astral.sh/uv/0.12.0/install.sh | sh"
    echo ""
    echo "  # Or using pip with pinned version"
    echo "  pip install --require-hashes -r requirements-uv.txt"
    echo ""
    echo "  # Or using Homebrew (macOS)"
    echo "  brew install uv"
    echo ""
    echo "After installing uv, run this script again."
    exit 1
fi

echo "✅ uv is installed: $(uv --version)"

# Check if Python 3.10+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python version: $PYTHON_VERSION"

# Check virtual environment status
echo "🔍 Checking virtual environment status..."

# Function to activate virtual environment
activate_venv() {
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
    
    # Verify activation worked
    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo "❌ Error: Failed to activate virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment activated: $VIRTUAL_ENV"
}

# Check if we're already in a virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "✅ Already in virtual environment: $VIRTUAL_ENV"
elif [[ -d ".venv" ]]; then
    echo "📦 Virtual environment exists, activating..."
    activate_venv
else
    echo "📦 Creating new virtual environment with uv..."
    uv venv
    activate_venv
fi

# Double-check we're in a virtual environment before proceeding
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "❌ Error: Not in a virtual environment. This is required to avoid system package conflicts."
    echo ""
    echo "🔧 To fix this, run:"
    echo "   ./scripts/setup-dev.sh    # This script should handle it automatically"
    echo "   # OR manually:"
    echo "   uv venv                   # Create virtual environment"
    echo "   source .venv/bin/activate # Activate it"
    echo "   ./scripts/setup-dev.sh    # Run this script again"
    exit 1
fi

# Install package in editable mode with development dependencies
echo "📦 Installing package in editable mode with uv..."
uv pip install -e ".[dev]"

# Install additional development tools
echo "🔧 Installing additional development tools..."
uv pip install bandit pip-audit

# Generate lock file for reproducible builds
echo "🔒 Generating lock file..."
uv lock

# Run initial tests
echo "🧪 Running initial tests..."
uv run pytest -v

# Run linting
echo "🔍 Running linting..."
uv run flake8 keychecker/ tests/

# Run type checking
echo "🔍 Running type checking..."
uv run mypy keychecker/

# Run security checks
echo "🔒 Running security checks..."
uv run bandit -r keychecker/ || echo "⚠️  Bandit found some issues (check output above)"
uv run pip-audit --skip-editable || echo "⚠️  pip-audit found some vulnerabilities (check output above)"
uv run pip-audit -r requirements-uv.txt || echo "⚠️  pip-audit found vulnerabilities in uv requirements"

echo ""
echo "✅ Development environment setup completed!"
echo ""
echo "📋 Next steps:"
echo "   - Activate virtual environment: source .venv/bin/activate"
echo "   - Run tests: ./scripts/test.sh"
echo "   - Build package: ./scripts/build.sh"
echo "   - Update version: ./scripts/version.sh <new_version>"
echo ""
echo "📋 Available scripts:"
echo "   - ./scripts/test.sh           - Run all tests and checks"
echo "   - ./scripts/clean.sh          - Clean virtual environment and cache"
echo "   - ./scripts/build.sh          - Build package for distribution"
echo "   - ./scripts/version.sh        - Update version number"
echo "   - ./scripts/publish-testpypi.sh - Publish to TestPyPI"
echo "   - ./scripts/publish-pypi.sh   - Publish to PyPI"
echo ""
echo "🚀 uv Commands:"
echo "   - uv run pytest               - Run tests"
echo "   - uv run black .              - Format code"
echo "   - uv run flake8 .             - Lint code"
echo "   - uv run mypy .               - Type check"
echo "   - uv add <package>            - Add new dependency"
echo "   - uv sync                     - Sync dependencies"
echo "   - uv lock                     - Update lock file"
echo "   - uv cache clean              - Clean cache"
