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

### Deprecated

### Removed

### Fixed

### Security
