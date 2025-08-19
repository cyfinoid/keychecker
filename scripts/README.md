# KeyChecker Development Scripts

This directory contains shell scripts to automate common development tasks for KeyChecker.

## 🚀 Quick Start

### Option 1: Using uv (Recommended - Faster)
```bash
# Install uv first
./scripts/install-uv.sh

# Set up development environment
./scripts/setup-dev-uv.sh

# Run tests
./scripts/test-uv.sh

# Clean environment (when needed)
./scripts/clean-uv.sh
```

### Option 2: Using pip (Traditional)
```bash
# Set up development environment
./scripts/setup-dev.sh

# Run tests
./scripts/test.sh
```

## Available Scripts

### 🚀 Setup and Development

#### `setup-dev-uv.sh` (Recommended)
Sets up the complete development environment using `uv` for faster dependency management.

```bash
./scripts/setup-dev-uv.sh
```

**What it does:**
- Checks for `uv` installation and provides installation instructions
- Creates virtual environment using `uv`
- Installs package in editable mode with development dependencies
- Installs additional development tools (bandit, safety)
- Generates lock file for reproducible builds
- Runs initial tests and checks

**Benefits of uv:**
- 10-100x faster dependency resolution
- Better dependency resolution algorithm
- Lock files for reproducible builds
- Built with Rust for performance

#### `clean-uv.sh`
Cleans the uv virtual environment and related files.

```bash
./scripts/clean-uv.sh [OPTIONS]
```

**Options:**
- `--venv-only` (default): Clean only the virtual environment
- `--all`: Clean virtual environment, lock file, and cache
- `--cache-only`: Clean only uv cache
- `--help`: Show help message

**What it does:**
- Removes virtual environment (.venv)
- Removes lock file (uv.lock) if specified
- Cleans uv cache if specified
- Removes pytest cache (.pytest_cache)
- Removes coverage reports (htmlcov)
- Removes mypy cache (.mypy_cache)
- Removes build artifacts (build/, dist/, *.egg-info)

**Examples:**
```bash
./scripts/clean-uv.sh              # Clean virtual environment only
./scripts/clean-uv.sh --all        # Clean everything
./scripts/clean-uv.sh --cache-only # Clean only cache
```

#### `install-uv.sh`
Cross-platform uv installation script.

```bash
./scripts/install-uv.sh
```

**What it does:**
- Detects OS and uses appropriate installation method
- Supports macOS (Homebrew/curl), Linux (curl), and Windows (pip)
- Verifies installation and provides next steps

#### `setup-dev.sh` (Legacy)
Sets up the complete development environment using traditional pip.

```bash
./scripts/setup-dev.sh
```

**What it does:**
- Creates virtual environment using `python -m venv`
- Installs package in editable mode with development dependencies
- Installs additional development tools (bandit, safety)
- Runs initial tests and checks

### 🧪 Testing and Quality

#### `test-uv.sh` (Recommended)
Runs all tests and quality checks using `uv` for faster execution.

```bash
./scripts/test-uv.sh
```

**What it does:**
- Runs code formatting check with black
- Runs flake8 linting
- Runs mypy type checking
- Runs pytest with coverage
- Runs security checks with bandit and safety

#### `test.sh` (Legacy)
Runs all tests and quality checks using traditional pip.

```bash
./scripts/test.sh
```

**What it does:**
- Runs pytest with coverage
- Runs flake8 linting
- Checks code formatting with black
- Runs mypy type checking
- Runs security checks with bandit (if available)

### 📦 Building and Distribution

#### `build.sh`
Builds the package for distribution.

```bash
./scripts/build.sh
```

**What it does:**
- Cleans previous builds
- Builds source distribution and wheel
- Validates package with twine
- Shows build results

#### `version.sh`
Updates version numbers in all relevant files.

```bash
./scripts/version.sh <new_version>
```

**Example:**
```bash
./scripts/version.sh 1.0.2
```

**What it does:**
- Updates version in `pyproject.toml`
- Updates version in `keychecker/__init__.py`
- Validates the changes
- Rebuilds package with new version

### 🚀 Publishing

#### `publish-testpypi.sh`
Publishes the package to TestPyPI for testing.

```bash
export TESTPYPI_API_TOKEN=your_token_here
./scripts/publish-testpypi.sh
```

**What it does:**
- Builds the package
- Uploads to TestPyPI
- Provides installation instructions

#### `publish-pypi.sh`
Publishes the package to PyPI.

```bash
export PYPI_API_TOKEN=your_token_here
./scripts/publish-pypi.sh
```

**What it does:**
- Builds the package
- Runs final verification tests
- Prompts for confirmation
- Uploads to PyPI
- Provides installation instructions

## Prerequisites

### Required Tools

#### For uv workflow (Recommended):
- Python 3.8+
- uv (install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

#### For pip workflow (Legacy):
- Python 3.8+
- pip
- build (for building packages)
- twine (for uploading to PyPI)

### Environment Variables
For publishing scripts, you need to set these environment variables:

```bash
# For TestPyPI
export TESTPYPI_API_TOKEN=your_testpypi_token_here

# For PyPI
export PYPI_API_TOKEN=your_pypi_token_here
```

## Usage Examples

### Complete Development Workflow with uv (Recommended)

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Set up development environment
./scripts/setup-dev-uv.sh

# 3. Run tests
./scripts/test-uv.sh

# 4. Build package
./scripts/build.sh

# 5. Update version (if needed)
./scripts/version.sh 1.0.2

# 6. Test on TestPyPI
export TESTPYPI_API_TOKEN=your_token
./scripts/publish-testpypi.sh

# 7. Publish to PyPI
export PYPI_API_TOKEN=your_token
./scripts/publish-pypi.sh
```

### Complete Development Workflow with pip (Legacy)

```bash
# 1. Set up development environment
./scripts/setup-dev.sh

# 2. Run tests
./scripts/test.sh

# 3. Build package
./scripts/build.sh

# 4. Update version (if needed)
./scripts/version.sh 1.0.2

# 5. Test on TestPyPI
export TESTPYPI_API_TOKEN=your_token
./scripts/publish-testpypi.sh

# 6. Publish to PyPI
export PYPI_API_TOKEN=your_token
./scripts/publish-pypi.sh
```

### Quick Testing

```bash
# Run all tests and checks with uv (faster)
./scripts/test-uv.sh

# Run all tests and checks with pip
./scripts/test.sh

# Build package
./scripts/build.sh
```

### Version Management

```bash
# Update to version 1.0.2
./scripts/version.sh 1.0.2

# Update to version 2.0.0
./scripts/version.sh 2.0.0
```

## uv Commands Reference

Once you have uv set up, you can use these commands directly:

```bash
# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run flake8 .

# Type check
uv run mypy .

# Add new dependency
uv add <package_name>

# Add development dependency
uv add --dev <package_name>

# Sync dependencies
uv sync

# Update lock file
uv lock

# Clean cache
uv cache clean

# Install in editable mode
uv pip install -e .
```

## GitHub Actions Integration

The scripts are designed to work with the GitHub Actions workflows:

- **CI Workflow** (`.github/workflows/ci.yml`): Runs on pull requests and pushes
- **Publish Workflow** (`.github/workflows/publish.yml`): Runs on releases

The GitHub Actions use the same commands as these scripts, ensuring consistency between local development and CI/CD.

## Migration from pip to uv

If you're migrating from the traditional pip setup to uv:

1. **Install uv:**
   ```bash
   ./scripts/install-uv.sh
   ```

2. **Remove old virtual environment:**
   ```bash
   rm -rf .venv
   ```

3. **Set up with uv:**
   ```bash
   ./scripts/setup-dev-uv.sh
   ```

4. **Use uv commands going forward:**
   ```bash
   ./scripts/test-uv.sh
   ```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Make sure scripts are executable
   ```bash
   chmod +x scripts/*.sh
   ```

2. **Python Not Found**: Ensure Python 3.8+ is installed and in PATH

3. **uv Not Found**: Install uv first
   ```bash
   ./scripts/install-uv.sh
   ```

4. **Missing Dependencies**: Run the appropriate setup script
   ```bash
   # For uv
   ./scripts/setup-dev-uv.sh
   
   # For pip
   ./scripts/setup-dev.sh
   ```

5. **Token Issues**: Ensure API tokens are set correctly
   ```bash
   echo $PYPI_API_TOKEN
   echo $TESTPYPI_API_TOKEN
   ```

### Getting Help

- Check the main [README.md](../Readme.md) for project overview
- Check GitHub Actions workflows for CI/CD configuration
- Visit [uv documentation](https://docs.astral.sh/uv/) for uv-specific help
