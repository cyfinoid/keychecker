#!/bin/bash

# Clean uv virtual environment script for KeyChecker
# This script cleans the uv virtual environment and related files

set -e

echo "🧹 Cleaning KeyChecker uv development environment..."

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --venv-only     Clean only the virtual environment (default)"
    echo "  --all           Clean virtual environment, lock file, and cache"
    echo "  --cache-only    Clean only uv cache"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Clean virtual environment only"
    echo "  $0 --all        # Clean everything (venv, lock, cache)"
    echo "  $0 --cache-only # Clean only uv cache"
}

# Parse command line arguments
CLEAN_VENV=true
CLEAN_LOCK=false
CLEAN_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --venv-only)
            CLEAN_VENV=true
            CLEAN_LOCK=false
            CLEAN_CACHE=false
            shift
            ;;
        --all)
            CLEAN_VENV=true
            CLEAN_LOCK=true
            CLEAN_CACHE=true
            shift
            ;;
        --cache-only)
            CLEAN_VENV=false
            CLEAN_LOCK=false
            CLEAN_CACHE=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

echo "📁 Current directory: $(pwd)"

# Clean virtual environment
if [ "$CLEAN_VENV" = true ]; then
    if [ -d ".venv" ]; then
        echo "🗑️  Removing virtual environment (.venv)..."
        rm -rf .venv
        echo "✅ Virtual environment removed"
    else
        echo "ℹ️  Virtual environment (.venv) not found"
    fi
fi

# Clean lock file
if [ "$CLEAN_LOCK" = true ]; then
    if [ -f "uv.lock" ]; then
        echo "🗑️  Removing lock file (uv.lock)..."
        rm -f uv.lock
        echo "✅ Lock file removed"
    else
        echo "ℹ️  Lock file (uv.lock) not found"
    fi
fi

# Clean uv cache
if [ "$CLEAN_CACHE" = true ]; then
    echo "🗑️  Cleaning uv cache..."
    uv cache clean
    echo "✅ uv cache cleaned"
fi

# Clean pytest cache
if [ -d ".pytest_cache" ]; then
    echo "🗑️  Removing pytest cache..."
    rm -rf .pytest_cache
    echo "✅ pytest cache removed"
fi

# Clean coverage reports
if [ -d "htmlcov" ]; then
    echo "🗑️  Removing coverage reports..."
    rm -rf htmlcov
    echo "✅ coverage reports removed"
fi

# Clean mypy cache
if [ -d ".mypy_cache" ]; then
    echo "🗑️  Removing mypy cache..."
    rm -rf .mypy_cache
    echo "✅ mypy cache removed"
fi

# Clean build artifacts
if [ -d "build" ]; then
    echo "🗑️  Removing build artifacts..."
    rm -rf build
    echo "✅ build artifacts removed"
fi

if [ -d "dist" ]; then
    echo "🗑️  Removing distribution files..."
    rm -rf dist
    echo "✅ distribution files removed"
fi

if [ -d "*.egg-info" ]; then
    echo "🗑️  Removing egg-info directories..."
    rm -rf *.egg-info
    echo "✅ egg-info directories removed"
fi

echo ""
echo "✅ Cleanup completed!"

# Show what was cleaned
echo ""
echo "📋 Summary of cleaned items:"
if [ "$CLEAN_VENV" = true ]; then
    echo "   - Virtual environment (.venv)"
fi
if [ "$CLEAN_LOCK" = true ]; then
    echo "   - Lock file (uv.lock)"
fi
if [ "$CLEAN_CACHE" = true ]; then
    echo "   - uv cache"
fi
echo "   - pytest cache (.pytest_cache)"
echo "   - coverage reports (htmlcov)"
echo "   - mypy cache (.mypy_cache)"
echo "   - build artifacts (build/, dist/, *.egg-info)"

echo ""
echo "🔄 To recreate the development environment:"
echo "   ./scripts/setup-dev-uv.sh"
