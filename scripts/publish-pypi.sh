#!/bin/bash

# PyPI publication script for KeyChecker
# This script publishes the package to PyPI

set -e

echo "🚀 Publishing KeyChecker to PyPI..."

# Check if required tools are installed
if ! command -v twine &> /dev/null; then
    echo "❌ Error: twine is not installed"
    echo "   Install with: pip install twine"
    exit 1
fi

# Build package
echo "🔨 Building package..."
./scripts/build.sh

# Check if PyPI token is set
if [ -z "$PYPI_API_TOKEN" ]; then
    echo "❌ Error: PYPI_API_TOKEN environment variable is not set"
    echo "   Set it with: export PYPI_API_TOKEN=your_token_here"
    exit 1
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
twine upload dist/*

echo "✅ Successfully published to PyPI!"
echo "🔗 Package available at: https://pypi.org/project/keychecker/"
echo ""
echo "📋 To install from PyPI:"
echo "   pip install keychecker"
