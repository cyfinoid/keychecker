# 🔑 KeyChecker

_A fast CLI tool to fingerprint SSH private keys and identify which Git hosting accounts they unlock (GitHub, GitLab, Bitbucket, Codeberg, Gitea, Hugging Face)._

> 🔬 **Part of Cyfinoid Research's Software Supply Chain Security Research**  
> This tool is created by [Cyfinoid Research](https://cyfinoid.com/research/software-supply-chain-security/) as part of our offensive tooling research focused on identification of next steps once an SSH private key is discovered. Learn more about our software supply chain security research and training programs.

---

## ✨ Features

### 🔍 Key Intelligence
- **Multi-format support**: OpenSSH, PEM, and DER private key formats
- **Key type detection**: `ed25519`, `rsa`, `ecdsa`, `dsa` with security analysis
- **Security validation**: Flags deprecated/insecure algorithms and weak key sizes
- **Passphrase detection**: Identifies if private keys are encrypted
- **Metadata extraction**: Public key, fingerprints (SHA256/MD5), and comments
- **Insight parsing**: Extracts local username, hostname, and IP addresses from comments

### 🌐 Account Discovery
- **Multi-provider support**: GitHub, GitLab, Bitbucket, Codeberg, Gitea, Hugging Face
- **Safe SSH handshakes**: Read-only validation without triggering repo operations
- **Username extraction**: Parses SSH identity banners to recover mapped usernames
- **Organization discovery**: Identifies user membership in organizations (GitHub API)

### 📁 Repository Discovery
- **Private repo detection**: Uses `git ls-remote` probes with wordlists
- **Concurrent scanning**: Configurable parallel connections for speed
- **Progress tracking**: Real-time progress bars during discovery
- **API integration**: GitHub token support for enhanced organization discovery

### 📊 Output Modes
- **Human-readable tables**: Clean, formatted output by default
- **CSV summary**: `--csv FILE` appends one machine-readable row per key
- **Exit codes**: Automation-friendly return codes
- **Verbose logging**: Debug and trace information
- **Public key export**: Save derived public keys to files

---

## 🚀 Quick Start

### Installation

```bash
# Using pipx (recommended for end users)
pipx install keychecker

# Using uv (recommended for developers)
uv add keychecker

# Using pip (legacy)
pip install --user keychecker

# From source (development)
git clone https://github.com/cyfinoid/keychecker
cd keychecker
./scripts/install.sh           # Install uv with pinned version & hashes
./scripts/setup-dev.sh         # Set up development environment
```

### Basic Usage

```bash
# Analyze a private key and Validate against servers (default behavior)
keychecker ~/.ssh/id_ed25519

# Validate against specific servers only (comma-separated, no spaces)
keychecker ~/.ssh/id_ed25519 --validate github,gitlab,bitbucket,codeberg,gitea,huggingface

# Validate against specific servers only
keychecker ~/.ssh/id_rsa --validate github,gitlab,huggingface

# Validate against every supported provider (all 19) — order doesn't matter
keychecker ~/.ssh/id_ed25519 --validate all
keychecker --validate all ~/.ssh/id_ed25519

# Append a CSV summary row (key path, fingerprint, provider:username / N)
keychecker ~/.ssh/id_ed25519 --validate all --csv results.csv

# Skip server validation (local analysis only)
keychecker ~/.ssh/id_ed25519 --no-validate
```

The `--csv` file grows by one row per run, so it composes with a shell loop to
scan a directory of keys into a single sheet:

```bash
for key in ~/keys/*; do
  keychecker "$key" --validate all --csv results.csv --no-banner --no-progress
done
# results.csv:
#   ~/keys/id_ed25519,SHA256:M7vOmp...,github:anantshri,gitlab:anant
#   ~/keys/id_rsa,SHA256:DE8Kf...,N
```

### Repository Discovery

```bash
# Discover private repositories on GitHub
keychecker ~/.ssh/id_rsa --validate github --discovery repo_names.txt

# Discover private repositories on Hugging Face
keychecker ~/.ssh/id_rsa --validate huggingface --discovery repo_names.txt

# With GitHub API token for enhanced organization discovery
export GITHUB_TOKEN=ghp_your_token_here
keychecker ~/.ssh/id_rsa --validate github --discovery repo_names.txt

# Or pass token directly
keychecker ~/.ssh/id_rsa --validate github --discovery repo_names.txt --github-token ghp_your_token_here
```

---

## 📖 Usage Reference

### Command Line Options

```bash
keychecker INPUT [OPTIONS]

Positional Arguments:
  INPUT                 Path to private key file

Options:
  -i, --input PATH      Path to private key file (alternative to positional)
  
  --validate PROVIDERS  Comma-separated server(s) to validate against, e.g.
                        "github" or "github,gitlab" (default: the six core
                        providers). Use "all" for every provider.
                        Choices: github, gitlab, bitbucket, codeberg, gitea,
                        huggingface, dataops, assembla, boltic, sourcehut,
                        notabug, azuredevops, framagit, gitverse, launchpad,
                        gitee, coding, codeup, gitflic, all
  --no-validate         Skip server validation (local analysis only)
  
  --discovery FILE      Enable repository discovery with wordlist file
                        (requires exactly one concrete --validate server)
  
  --github-token TOKEN  GitHub API token for enhanced organization discovery
  --no-progress         Disable progress bars during repository discovery
  
  --public-out FILE     Save derived public key to file
  --csv FILE            Append a CSV summary row for the key: key path,
                        SHA256 fingerprint, then one "provider:username" per
                        identified account, or a single "N" if none found
  --no-banner           Suppress banner output
  
  --timeout SECONDS     Per-connection timeout (default: 5)
  --concurrency N       Parallel connections (default: 10)
  
  -v, --verbose         Enable debug/trace logs
  -V, --version         Show version number and exit
  -h, --help            Show help message
```

### Examples

```bash
# Basic key analysis
keychecker ~/.ssh/id_ed25519

# Validate against GitHub only
keychecker ~/.ssh/id_rsa --validate github

# Validate against Hugging Face only
keychecker ~/.ssh/id_rsa --validate huggingface

# Validate against every supported provider and record a CSV row
keychecker ~/.ssh/id_rsa --validate all --csv results.csv

# Discover repositories with custom wordlist
keychecker ~/.ssh/id_rsa --validate github --discovery my_repos.txt

# Discover repositories on Hugging Face
keychecker ~/.ssh/id_rsa --validate huggingface --discovery my_repos.txt

# Save public key to file
keychecker ~/.ssh/id_ed25519 --public-out my_key.pub

# Verbose output with custom timeout
keychecker ~/.ssh/id_rsa --validate github --timeout 10 --verbose

# Check version
keychecker --version
```

---

## 🌍 Supported Servers

| Server | Host | Features | Notes |
|--------|------|----------|-------|
| **GitHub** | `git@github.com` | Username extraction, Organization discovery | SaaS platform |
| **GitLab** | `git@gitlab.com` | Username extraction | SaaS and Selfhostable platform |
| **Bitbucket** | `git@bitbucket.org` | Key confirmation | SaaS Platform |
| **Codeberg** | `git@codeberg.org` | Username extraction | SaaS based on forgejo |
| **Gitea** | `git@gitea.com` | Username extraction | Saas based on Gitea |
| **Hugging Face** | `git@hf.co` | Username extraction | AI/ML model hosting platform |
| **DataOps.live** | `git@app.dataops.live` | Key confirmation | Data engineering platform |
| **Assembla** | `git@git.assembla.com` | Username extraction | Source code & collaboration platform |
| **Boltic** | `git@ssh.git.boltic.io` | Key confirmation | Serverless platform (Fynd Boltic) |
| **SourceHut** | `git@git.sr.ht` | Username extraction | Open source forge |
| **NotABug** | `git@notabug.org` | Username extraction | Gitea-based free code hosting |
| **Azure DevOps** | `git@ssh.dev.azure.com` | Key confirmation | Microsoft DevOps platform |
| **Framagit** | `git@framagit.org` | Username extraction | GitLab-based forge by Framasoft |
| **GitVerse** | `git@gitverse.ru` | Key confirmation | Russian Git platform by SberTech |
| **Launchpad** | `git@git.launchpad.net` | Key confirmation | Canonical/Ubuntu code hosting |
| **Gitee** 🇨🇳 | `git@gitee.com` | Username extraction | Chinese Git platform (OSCHINA) |
| **CODING.net** 🇨🇳 | `git@e.coding.net` | Key confirmation | Chinese DevOps platform (Tencent) |
| **CodeUP** 🇨🇳 | `git@codeup.aliyun.com` | Username extraction | Chinese DevOps Git (Alibaba Cloud) |
| **GitFlic** 🇷🇺 | `git@gitflic.ru` | Key confirmation | Russian Git hosting platform |

---

## 📋 Example Output

### Key Analysis
```
🔑 KeyChecker - SSH Key Analysis Tool
=====================================

Key: ~/.ssh/id_ed25519
Type: ed25519
Bits: 256
Passphrase: NO
Public: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... comment='user@hostname'
Comment: user@hostname
SHA256: SHA256:abc123...
MD5: MD5:12:34:56:78:9a:bc:de:f0

Insights: local_user=user, host=hostname
```

### Server Validation
```
Validation:
- github: username=john_doe ✅
- gitlab: username=jane_smith ✅
- bitbucket: auth success, username=? (repo path required)
- huggingface: username=anantshri ✅
```

### Repository Discovery
```
Organization Discovery:
- Personal repositories: john_doe
- Organizations: acme-corp, open-source-proj

Repository Discovery:
Found 3 accessible repositories:
- john_doe/secret-project (private)
- acme-corp/internal-tools (private)
- acme-corp/api-service (private)
```

---

## 🔐 Security Notes

- **Read-only operations**: No repositorywrite operations performed
- **Local processing**: Private keys are processed in-memory, never uploaded
- **Authorized use only**: Only use against keys you own or are authorized to test
- **SSH handshake logging**: Some providers may log SSH connections - use responsibly

---

## 🛠 Development

### Setup Development Environment

```bash
git clone https://github.com/cyfinoid/keychecker
cd keychecker

# Install uv (if not already installed)
./scripts/install.sh

# Set up development environment
./scripts/setup-dev.sh

# Run tests
./scripts/test.sh

# Run demo
uv run python examples/demo.py
```

### Project Structure

```
keychecker/
├── keychecker/
│   ├── core/           # Core analysis and validation logic
│   ├── plugins/        # Git hosting provider implementations
│   ├── utils/          # Output formatting and utilities
│   ├── cli.py          # Command-line interface
│   └── __main__.py     # Entry point
├── examples/           # Usage examples and sample data
├── tests/              # Test suite
└── docs/               # Documentation
```

### Adding New Providers

KeyChecker uses a plugin architecture for Git hosting providers. To add a new provider:

1. Create a new provider class in `keychecker/plugins/`
2. Inherit from `BaseGitProvider`
3. Implement required methods: `validate_key()`, `identify_user()`, `discover_organizations()`
4. Register the provider in `keychecker/plugins/__init__.py`

### Development Scripts

The project includes shell scripts to automate common tasks:

```bash
# Install uv (if needed)
./scripts/install.sh

# Set up development environment
./scripts/setup-dev.sh

# Run tests and quality checks
./scripts/test.sh

# Clean development environment
./scripts/clean.sh

# Build package for distribution
./scripts/build.sh

# Update version number
./scripts/version.sh 1.0.2
```

## Release Workflow

```bash
# Test publication workflow (recommended)
# 1. Use GitHub Actions to publish to TestPyPI:
#    - Go to Actions tab → "Publish to PyPI" → "Run workflow"
#    - Enter a test version (e.g., 1.0.2-rc1)
#    - This will test installation with pip, pipx, and uv (with --pre flag for pre-releases)
# 2. Create a GitHub release to publish to PyPI:
#    - Version consistency is automatically verified
#    - Production publication with full testing (stable versions only)
```
### Alternatives

```bash
# Manual publication (alternative)
export TESTPYPI_API_TOKEN=your_token
./scripts/publish-testpypi.sh

export PYPI_API_TOKEN=your_token
./scripts/publish-pypi.sh
```

See `scripts/README.md` for detailed script documentation.

---

## 📊 Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Runtime/IO/argument error |
| `2` | All servers unreachable |
| `3` | Repository discovery attempted, no repositories found |
| `4` | Key parsed but flagged (deprecated/insecure) |

---

## 🗺️ Roadmap

- **Self-hosted environments**: Support for custom GitLab, Bitbucket, and Gitea instances
- **Arbitrary hosts**: Generic SSH server validation with custom host/port configuration
- **Host discovery**: Automatic detection of Git server type and capabilities
- **Cloud Git platforms**: Support for Azure DevOps, AWS CodeCommit, Google Cloud Source Repositories
- **Enterprise platforms**: Integration with enterprise Git solutions
- **Public repository filtering**: Skip public repositories during discovery (no point in bruteforcing)
- **Intelligent wordlists**: Generate repository name candidates based on discovered organizations
- **Rate limit awareness**: Adaptive discovery speed based on server rate limits

### Quality of Life Improvement

- **OIDC Publication**: Move publication and release to OIDC aware setup

---


## 🤖 AI-Assisted Development

This project was developed with the assistance of AI tools, most notably **Cursor IDE**, **Claude Code**, and **Qwen3-Coder**. These tools helped accelerate development and improve velocity. All AI-generated code has been carefully reviewed and validated through human inspection to ensure it aligns with the project’s intended functionality and quality standards.

---
## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup
git clone https://github.com/cyfinoid/keychecker
cd keychecker

# Install uv and setup development environment
./scripts/install.sh
./scripts/setup-dev.sh

# Run tests
./scripts/test.sh
```

#### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `./scripts/test.sh`
6. Submit a pull request

For detailed development instructions, see [scripts/README.md](scripts/README.md).

---

## 💬 Community & Discussion

Join our Discord server for discussions, questions, and collaboration:

**[Join our Discord Server](https://discord.gg/7trkcUFrgR)**

Connect with other security researchers, share your findings, and get help with KeyChecker usage and development.

---

## 🙏 Acknowledgments & Contributions

### Contributors

We'd like to thank the following contributors for their valuable input and support:

- **[Kumar Ashwin](https://github.com/0xcardinal/)** - Initial ideation and help with PoC building

---

## 📄 License

This project is licensed under the GNU General Public License v3 (GPLv3) - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This tool is designed for security auditing and penetration testing of systems you own or have explicit permission to test. Always ensure you have proper authorization before using this tool against any systems or keys you don't own.

The authors are not responsible for any misuse of this software.

---

## 🔬 Cyfinoid Research

**Cutting-Edge Software Supply Chain Security Research**

Pioneering advanced software supply chain security research and developing innovative offensive security tools for the community.

This tool is part of our free research toolkit - helping security researchers and penetration testers identify next steps after discovering SSH private keys.

### 🌐 Software Supply Chain Focus

Specializing in software supply chain attacks, CI/CD pipeline security, and offensive security research.

Our research tools help organizations understand their software supply chain vulnerabilities and develop effective defense strategies.

### 🎓 Learn & Explore

Explore our professional training programs, latest research insights, and free open source tools developed from our cutting-edge cybersecurity research.

**[Upcoming Trainings](https://cyfinoid.com/trainings/#upcoming-trainings)** | **[Read Our Blog](https://cyfinoid.com/blog/)** | **[Open Source by Cyfinoid](https://cyfinoid.com/open-source/)**

Hands-on training in software supply chain security, CI/CD pipeline attacks, and offensive security techniques

© 2025 Cyfinoid Research. KeyChecker - Free Software Supply Chain Security Research Tool
