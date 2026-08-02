#!/bin/bash

# Install uv script for KeyChecker
# This script helps install uv on different platforms

set -e

# Version of uv to install. This is the single source of truth for the
# development toolchain; keep it in sync with requirements-uv.txt (hashed
# pin) and the [tool.uv] required-version in pyproject.toml.
UV_VERSION="0.12.0"

echo "🚀 Installing uv for KeyChecker development..."

# Check if uv is already installed
if command -v uv &> /dev/null; then
    echo "✅ uv is already installed: $(uv --version)"
    exit 0
fi

# Detect operating system
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "🖥️  Detected OS: $OS"
echo "🏗️  Detected Architecture: $ARCH"

# Install uv based on OS
case "$OS" in
    "Darwin")
        echo "🍎 Installing uv on macOS..."
        if command -v brew &> /dev/null; then
            echo "📦 Using Homebrew..."
            brew install uv
        else
            echo "📦 Using versioned curl installer..."
            curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh
        fi
        ;;
    "Linux")
        echo "🐧 Installing uv on Linux..."
        curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh
        ;;
    "MINGW"*|"MSYS"*|"CYGWIN"*)
        echo "🪟 Installing uv on Windows..."
        echo "📦 Using pip with pinned version and hashes..."
        if [ -f "requirements-uv.txt" ]; then
            pip install --require-hashes -r requirements-uv.txt
        else
            echo "⚠️  requirements-uv.txt not found, using fallback installation..."
            pip install "uv==${UV_VERSION}"
        fi
        ;;
    *)
        echo "❌ Unsupported operating system: $OS"
        echo "Please install uv manually:"
        echo "  - Visit: https://docs.astral.sh/uv/getting-started/installation/"
        echo "  - Or use: pip install --require-hashes -r requirements-uv.txt"
        exit 1
        ;;
esac

# Verify installation
if command -v uv &> /dev/null; then
    echo "✅ uv installed successfully: $(uv --version)"
    echo ""
    echo "🎉 You can now set up the development environment:"
    echo "   ./scripts/setup-dev.sh"
else
    echo "❌ uv installation failed"
    echo "Please install uv manually:"
    echo "  - Visit: https://docs.astral.sh/uv/getting-started/installation/"
    echo "  - Or use: pip install --require-hashes -r requirements-uv.txt"
    exit 1
fi
