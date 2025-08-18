#!/bin/bash

# Development setup script for KeyChecker
# This script sets up the development environment

set -e

echo "🚀 Setting up KeyChecker development environment..."

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install package in editable mode with development dependencies
echo "📦 Installing package in editable mode..."
pip install -e ".[dev]"

# Install additional development tools
echo "🔧 Installing additional development tools..."
pip install bandit safety

# Run initial tests
echo "🧪 Running initial tests..."
pytest -v

# Run linting
echo "🔍 Running linting..."
flake8 keychecker/ tests/

# Run type checking
echo "🔍 Running type checking..."
mypy keychecker/

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
echo "   - ./scripts/test.sh          - Run all tests and checks"
echo "   - ./scripts/build.sh         - Build package for distribution"
echo "   - ./scripts/version.sh       - Update version number"
echo "   - ./scripts/publish-testpypi.sh - Publish to TestPyPI"
echo "   - ./scripts/publish-pypi.sh  - Publish to PyPI"
