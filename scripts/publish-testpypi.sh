#!/bin/bash

# TestPyPI publication script for KeyChecker
# This script publishes the package to TestPyPI for testing

set -e

echo "🚀 Publishing KeyChecker to TestPyPI..."

# Check if required tools are installed
if ! command -v twine &> /dev/null; then
    echo "❌ Error: twine is not installed"
    echo "   Install with: pip install twine"
    exit 1
fi

# Build package
echo "🔨 Building package..."
./scripts/build.sh

# Check if TestPyPI token is set
if [ -z "$TESTPYPI_API_TOKEN" ]; then
    echo "❌ Error: TESTPYPI_API_TOKEN environment variable is not set"
    echo "   Set it with: export TESTPYPI_API_TOKEN=your_token_here"
    exit 1
fi

# Upload to TestPyPI
echo "📤 Uploading to TestPyPI..."
twine upload --repository testpypi dist/*

echo "✅ Successfully published to TestPyPI!"
echo "🔗 Package available at: https://test.pypi.org/project/keychecker/"
echo ""
echo "📋 To test installation from TestPyPI:"
echo "   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ keychecker"
