# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Keep this file high-level: one bullet per user-visible change, grouped under the
right heading. Record the blow-by-blow detail (commands, diffs, reasoning) in
`DETAILED_CHANGELOG.md` instead.

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [1.5.0] - 2026-10-06

### Added

- Library deprecation warnings (e.g. cryptography's "SSH DSA key support is
  deprecated") are now consumed during key analysis and surfaced as ⚠️ lines
  in the output instead of leaking to stderr as raw Python warnings
  (`warnings` key in the analysis result). From PR #45 by @ai-anant.
- Encrypted PKCS#8 keys (`-----BEGIN ENCRYPTED PRIVATE KEY-----`, OpenSSL's
  `genpkey -aes*` output) are now identified as `pkcs8` instead of `unknown`.
  From PR #45 by @ai-anant.
- `--validate all` keyword that expands to every supported provider (all 19),
  instead of only the six core providers scanned by default.
- `--csv FILE` option that appends a one-line CSV summary per key: key path,
  SHA256 fingerprint, then a `provider:username` entry for each identified
  account, or a single `N` when no username is found.
- `--org ORG` option (repeatable / comma-separated) to target custom
  organization name(s) during repository discovery, merged with API-discovered
  orgs by default. Requires `--discovery`.
- `--no-org-discovery` flag to skip automatic organization discovery and test
  only the org(s) supplied with `--org`.

### Changed

- Lint tooling switched from flake8 + black to **ruff** (check + format),
  credited to @prgyn8's PR #5 (uv-cache part of that PR declined; see
  DETAILED_CHANGELOG). `ruff` is configured to mirror the previous flake8
  gate (`E,F,W` @ 88 chars, same excludes); ruff 0.16's broader default rule
  sets are deliberately not enabled yet. One-time `ruff format` pass
  normalized quote style in 20 files (no logic changes); `.flake8`,
  `[tool.black]`, and the black/flake8 dev dependencies were removed.
- `--validate` now takes a single comma-separated value (e.g. `github,gitlab`)
  instead of space-separated tokens. This lets the key file follow the flag —
  `keychecker --validate all <file>` now works in any argument order, where
  previously the flag greedily consumed the path and errored.
- Multi-provider validation (`--validate all` and comma-separated lists) now
  runs providers concurrently, bounded by `--concurrency`, instead of one at a
  time — noticeably faster when validating against many providers.
- Upgraded dependencies, superseding the open dependabot PRs #50–#55 while
  honoring the lock's 7-day `exclude-newer-span` supply-chain policy (releases
  published after 2026-09-29 were deliberately not adopted): cryptography
  49.0.0 → 50.0.1, aiohttp 3.14.2 → 3.14.3 (pulls yarl 1.25.1), tqdm 4.69.0 →
  4.70.1, types-tqdm → 4.70.0.20260906 (drops its types-requests dependency),
  and uv-managed pip 26.1.2 → 26.2.1. Minimum-version specifiers in
  `pyproject.toml` and `requirements.txt` updated to match.
- uv pinned for hashed/Windows installation and CI bumped to 0.12.23:
  refreshed `requirements-uv.txt` (new version + PyPI hashes), the stale
  fallback pin in `scripts/install.sh` (was 0.11.32), the `setup-uv` version
  in `ci.yml`/`publish.yml` (was 0.12.0), and `scripts/README.md`. Still
  inside the supported `>=0.12.0,<0.13.0` range.
- Regenerated the checked-in `sbom/` SBOMs via `scripts/ci/aidc-sbom-all.sh`
  from a clean tree so they reflect the new dependency versions.

### Deprecated

### Removed

### Fixed

- Editable/wheel build no longer fails with "Multiple top-level packages
  discovered in a flat-layout" — package discovery is now pinned to
  `keychecker*` so the `logs/` directory is not treated as a package. Also
  pointed `license` at the actual `LICENSE` file (was the nonexistent
  `LICENSE.md`) using the SPDX-string form.

### Security

- Transitive lock upgrades closing all `pip-audit` findings:
  multidict 6.7.1 → 6.9.1 (CVE-2026-104874, reference-leak memory
  exhaustion in items-view set operations; fix release 6.9.1 — 7.0.0 is
  excluded by aiohttp's own `multidict<7.0` cap) and urllib3 2.7.0 → 2.8.0
  (PYSEC-2026-4175 proxy-TLS config mixups, PYSEC-2026-4176 Deflate
  infinite loop, PYSEC-2026-4177 unbounded chunk-size buffering). Both
  fix releases predate the lock's 7-day `exclude-newer-span` cutoff, so no
  policy bypass was needed. `pip-audit` on the locked set is now clean.
- uv-managed pip upgraded 26.1.2 → 26.2.1 in `uv.lock`; 26.1.2 is affected by
  published advisory PYSEC-2026-3721 (fix: 26.2).
- `publish.yml`: workflow inputs/context (`github.event.inputs.version`,
  `github.event.release.tag_name`) are now passed to `run:` steps through
  `env:` variables instead of direct `${{ ... }}` interpolation, closing
  shell-injection vectors flagged by semgrep / fresh-eyes review.
