#!/bin/bash

# PyPI publication script for KeyChecker
# This script publishes the package to PyPI

set -e

echo "🚀 Publishing KeyChecker to PyPI..."

# Check if required tools are installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Please run ./scripts/install.sh first"
    exit 1
fi

# Check if twine is available
if ! uv run twine --version &> /dev/null; then
    echo "❌ Error: twine is not installed in the virtual environment"
    echo "Please run ./scripts/setup-dev.sh first"
    exit 1
fi

# Build package
echo "🔨 Building package..."
./scripts/build.sh

# Check if PyPI token is set
if [ -z "$PYPI_API_TOKEN" ]; then
    if ! grep -q "^\[pypi\]" ~/.pypirc 2>/dev/null; then
        echo "❌ Error: PYPI_API_TOKEN environment variable is not set and no [pypi] section found in ~/.pypirc"
        echo "   Set it with: export PYPI_API_TOKEN=your_token_here"
        echo "   Or configure ~/.pypirc with [pypi] credentials"
        exit 1
    fi
fi

# Final verification
echo "🔍 Running final verification..."
./scripts/test.sh

# Confirm before publishing
echo ""
echo "⚠️  WARNING: This will publish to the official PyPI repository!"
echo "   This action cannot be undone."
echo ""
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Publication cancelled"
    exit 1
fi

# Upload to PyPI
echo "📤 Uploading to PyPI..."
uv run twine upload dist/*

echo "✅ Successfully published to PyPI!"
echo "🔗 Package available at: https://pypi.org/project/keychecker/"
echo ""
echo "📋 To install from PyPI:"
echo "   pip install keychecker"
