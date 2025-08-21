#!/bin/bash

# Version update script for KeyChecker
# This script updates version numbers in all relevant files

set -e

if [ $# -eq 0 ]; then
    echo "❌ Error: Version number required"
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.2"
    exit 1
fi

NEW_VERSION=$1

# Validate version format (basic check)
if [[ ! $NEW_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Invalid version format. Use MAJOR.MINOR.PATCH (e.g., 1.0.2)"
    exit 1
fi

echo "🔄 Updating version to $NEW_VERSION..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Please run ./scripts/install.sh first"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(uv run python -c "import keychecker; print(keychecker.__version__)")
echo "📋 Current version: $CURRENT_VERSION"
echo "📋 New version: $NEW_VERSION"

# Update version in pyproject.toml
echo "📝 Updating pyproject.toml..."
sed -i.bak "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
rm pyproject.toml.bak

# Update version in keychecker/__init__.py
echo "📝 Updating keychecker/__init__.py..."
sed -i.bak "s/__version__ = \"$CURRENT_VERSION\"/__version__ = \"$NEW_VERSION\"/" keychecker/__init__.py
rm keychecker/__init__.py.bak

# Verify the changes
echo "✅ Verifying version update..."
NEW_VERSION_CHECK=$(uv run python -c "import keychecker; print(keychecker.__version__)")
if [ "$NEW_VERSION_CHECK" = "$NEW_VERSION" ]; then
    echo "✅ Version successfully updated to $NEW_VERSION"
else
    echo "❌ Error: Version update failed"
    exit 1
fi

# Clean and rebuild
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

echo "📦 Building package with new version..."
uv build

echo "✅ Version update completed successfully!"
echo "📋 New distribution files created in dist/ directory"
