# 🔑 KeyChecker

_A fast CLI to fingerprint SSH private keys and identify which Git hosting accounts they unlock (GitHub, GitLab, Bitbucket, …)._

---

## ✨ Features

- **Key intelligence**
  - Detect key type (`ed25519`, `rsa`, `ecdsa`, `dsa`) and flag deprecated/insecure keys.
  - Check if the private key is passphrase-protected.
  - Extract public key and **comment** (local username, hostname, IP, etc.).

- **Account discovery**
  - Safely handshake with Git servers (GitHub, GitLab, Bitbucket, …).
  - Parse SSH identity banner to recover mapped **username/handle**.
  - Read-only checks – no repo operations triggered.

- **Bruteforce module**
  - Use `git ls-remote` probes with a candidate username list.
  - Useful for servers that require repo paths to validate identity.

- **Output modes**
  - Human-readable table by default.
  - JSON mode (`--json`) for CI/CD pipelines.
  - Exit codes for automation.

---

## 🚀 Quick Start

Install:

```bash
pipx install keychecker
# or
pip install --user keychecker
```

Basic usage (local analysis only):

```bash
keychecker -i ~/.ssh/id_ed25519
```

Validate against servers:

```bash
keychecker -i ~/.ssh/id_ed25519 --validate github gitlab bitbucket
```

Bruteforce mode:

```
keychecker -i ~/.ssh/id_rsa --bruteforce --server gitlab --wordlist usernames.txt
```


⚙️ Usage
```bash
keychecker -i INPUT [--validate SERVERS…] [--bruteforce --server NAME --wordlist FILE]
            [--timeout SEC] [--json] [--public-out FILE] [--no-banner]
            [--known-hosts PATH] [--concurrency N] [--verbose]
```

Options

-i, --input Path to private key file (required).

--validate One or more servers (github, gitlab, bitbucket).

--bruteforce Enable username enumeration strategy.

--server Server shortname (used with --bruteforce).

--wordlist File with candidate usernames.

--json JSON output mode.

--timeout Per-connection timeout (default: 5s).

--public-out Save derived public key to file.

--concurrency Parallel connections (default: auto).

--verbose, -v Debug/trace logs.

🌍 Supported Servers
Shortname	Host	Notes
github	git@github.com	Reveals GitHub username in banner.
gitlab	git@gitlab.com	May require repo path, bruteforce helps
bitbucket	git@bitbucket.org	Similar to GitLab behavior.
📋 Example Output

Human readable:

Key: ./keys/id_ed25519
Type: ed25519
Passphrase: NO
Public: ssh-ed25519 AAAAC3Nza... comment='runner@build-01'
Insights: local_user=runner, host=build-01

Validation:
- github: username ✅
- gitlab: auth success, username=? (repo path required)


JSON mode:

{
  "input": "./keys/id_ed25519",
  "key": {"type": "ed25519", "bits": 256, "passphrase": false},
  "public_key": {"fingerprint_sha256": "SHA256:abc...", "comment": "runner@build-01"},
  "validation": {
    "github": {"reachable": true, "username": "anantshri"},
    "gitlab": {"reachable": true, "username": null}
  }
}

❗ Exit Codes

0 – success

1 – runtime/IO/argument error

2 – all servers unreachable

3 – bruteforce attempted, no match found

4 – key parsed but flagged (deprecated/insecure)

🔐 Security Notes

Read-only checks. No repository access or write operations.

Only use against keys you own or are authorized to test.

Private keys are processed in-memory; never uploaded.

Some providers may log SSH handshakes – use responsibly.

🛠 Development

Clone and install in editable mode:

git clone https://github.com/cyfinoid/keychecker
cd keychecker
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q

📌 Roadmap

Self-hosted GitLab/Bitbucket (--host / --port).

Smarter bruteforce with public repo heuristics.

SBOM-friendly JSON/CycloneDX output.

Bulk audit mode for orgs.

📜 License

MIT
