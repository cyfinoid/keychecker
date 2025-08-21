#!/bin/bash

# Build script for KeyChecker
# This script builds the package for distribution

set -e

echo "🔨 Building KeyChecker package..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Please run ./scripts/install.sh first"
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Build package using uv
echo "📦 Building package..."
uv build

# Check package using uv
echo "✅ Checking package..."
uv run twine check dist/*

# Show build results
echo "📋 Build results:"
ls -la dist/

echo "✅ Build completed successfully!"
echo "📦 Distribution files created in dist/ directory"
