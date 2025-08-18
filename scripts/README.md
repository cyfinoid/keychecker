# KeyChecker Development Scripts

This directory contains shell scripts to automate common development tasks for KeyChecker.

## Available Scripts

### 🚀 Setup and Development

#### `setup-dev.sh`
Sets up the complete development environment for new contributors.

```bash
./scripts/setup-dev.sh
```

**What it does:**
- Creates virtual environment
- Installs package in editable mode with development dependencies
- Installs additional development tools (bandit, safety)
- Runs initial tests and checks

### 🧪 Testing and Quality

#### `test.sh`
Runs all tests and quality checks.

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

### Complete Development Workflow

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
# Run all tests and checks
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

## GitHub Actions Integration

The scripts are designed to work with the GitHub Actions workflows:

- **CI Workflow** (`.github/workflows/ci.yml`): Runs on pull requests and pushes
- **Publish Workflow** (`.github/workflows/publish.yml`): Runs on releases

The GitHub Actions use the same commands as these scripts, ensuring consistency between local development and CI/CD.

## Troubleshooting

### Common Issues

1. **Permission Denied**: Make sure scripts are executable
   ```bash
   chmod +x scripts/*.sh
   ```

2. **Python Not Found**: Ensure Python 3.8+ is installed and in PATH

3. **Missing Dependencies**: Run the setup script
   ```bash
   ./scripts/setup-dev.sh
   ```

4. **Token Issues**: Ensure API tokens are set correctly
   ```bash
   echo $PYPI_API_TOKEN
   echo $TESTPYPI_API_TOKEN
   ```

### Getting Help

- Check the main [README.md](../Readme.md) for project overview
- Check GitHub Actions workflows for CI/CD configuration
