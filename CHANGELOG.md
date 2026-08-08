# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Keep this file high-level: one bullet per user-visible change, grouped under the
right heading. Record the blow-by-blow detail (commands, diffs, reasoning) in
`DETAILED_CHANGELOG.md` instead.

## [Unreleased]

### Added

- `--validate all` keyword that expands to every supported provider (all 19),
  instead of only the six core providers scanned by default.
- `--csv FILE` option that appends a one-line CSV summary per key: key path,
  SHA256 fingerprint, then a `provider:username` entry for each identified
  account, or a single `N` when no username is found.

### Changed

- `--validate` now takes a single comma-separated value (e.g. `github,gitlab`)
  instead of space-separated tokens. This lets the key file follow the flag —
  `keychecker --validate all <file>` now works in any argument order, where
  previously the flag greedily consumed the path and errored.

### Deprecated

### Removed

### Fixed

- Editable/wheel build no longer fails with "Multiple top-level packages
  discovered in a flat-layout" — package discovery is now pinned to
  `keychecker*` so the `logs/` directory is not treated as a package. Also
  pointed `license` at the actual `LICENSE` file (was the nonexistent
  `LICENSE.md`) using the SPDX-string form.

### Security
