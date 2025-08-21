#!/bin/bash

# TestPyPI publication script for KeyChecker
# This script publishes the package to TestPyPI for testing

set -e

echo "🚀 Publishing KeyChecker to TestPyPI..."

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

# Check if TestPyPI token is set
# Check if TESTPYPI_API_TOKEN is set or if ~/.pypirc has [testpypi] section
if [ -z "$TESTPYPI_API_TOKEN" ]; then
    if ! grep -q "^\[testpypi\]" ~/.pypirc 2>/dev/null; then
        echo "❌ Error: TESTPYPI_API_TOKEN environment variable is not set and no [testpypi] section found in ~/.pypirc"
        echo "   Set it with: export TESTPYPI_API_TOKEN=your_token_here"
        echo "   Or configure ~/.pypirc with [testpypi] credentials"
        exit 1
    fi
fi

# Final verification
echo "🔍 Running final verification..."
./scripts/test.sh

# Upload to TestPyPI
echo "📤 Uploading to TestPyPI..."
uv run twine upload --repository testpypi dist/*

echo "✅ Successfully published to TestPyPI!"
echo "🔗 Package available at: https://test.pypi.org/project/keychecker/"
echo ""
echo "📋 To test installation from TestPyPI:"
echo "   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ keychecker"
