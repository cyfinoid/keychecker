#!/bin/bash

# Development setup script for KeyChecker using uv
# This script sets up the development environment with uv for faster dependency management

set -e

echo "🚀 Setting up KeyChecker development environment with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo ""
    echo "📦 Installing uv..."
    echo "Please install uv first:"
    echo ""
    echo "  # Using curl (recommended)"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "  # Or using pip"
    echo "  pip install uv"
    echo ""
    echo "  # Or using Homebrew (macOS)"
    echo "  brew install uv"
    echo ""
    echo "After installing uv, run this script again."
    exit 1
fi

echo "✅ uv is installed: $(uv --version)"

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python version: $PYTHON_VERSION"

# Create virtual environment using uv
echo "📦 Creating virtual environment with uv..."
uv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install package in editable mode with development dependencies
echo "📦 Installing package in editable mode with uv..."
uv pip install -e ".[dev]"

# Install additional development tools
echo "🔧 Installing additional development tools..."
uv pip install bandit safety

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
uv run safety check || echo "⚠️  Safety found some issues (check output above)"

echo ""
echo "✅ Development environment setup completed with uv!"
echo ""
echo "📋 Next steps:"
echo "   - Activate virtual environment: source .venv/bin/activate"
echo "   - Run tests: ./scripts/test-uv.sh"
echo "   - Build package: ./scripts/build.sh"
echo "   - Update version: ./scripts/version.sh <new_version>"
echo ""
echo "📋 Available scripts:"
echo "   - ./scripts/test-uv.sh        - Run all tests and checks with uv"
echo "   - ./scripts/test.sh           - Run all tests and checks with pip"
echo "   - ./scripts/clean-uv.sh       - Clean virtual environment and cache"
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
