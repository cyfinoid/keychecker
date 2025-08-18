#!/bin/bash

# Build script for KeyChecker
# This script builds the package for distribution

set -e

echo "🔨 Building KeyChecker package..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Build package
echo "📦 Building package..."
python3 -m build

# Check package
echo "✅ Checking package..."
python3 -m twine check dist/*

# Show build results
echo "📋 Build results:"
ls -la dist/

echo "✅ Build completed successfully!"
echo "📦 Distribution files created in dist/ directory"
