# 2026-08-15 — Parallel provider validation + custom-org discovery

## Symptom / goal

Two requests:

1. "Can we do a parallel check for all service providers or do we need to run
   them one by one only?"
2. "An option to specify a custom org name instead of discovering via API."

Item 1 turned out to be both a question and a feature request; item 2 a feature
request. Confirmed scope with the user: implement both; for custom orgs, default
to merging with API discovery and add a `--no-org-discovery` switch to skip it.

## Diagnosis

- **Parallelism:** the CLI validates via `ServerValidator.validate_servers_streaming`,
  which looped over providers and `await`ed each `validate_key` sequentially
  (explicit comment: "Execute validations sequentially to avoid terminal output
  interference"). The older `validate_servers` also ran serially despite its
  "concurrently" docstring. Progress bars are already disabled during validation
  in `cli.py` (`provider._progress_enabled = False`), so the output-interference
  rationale no longer holds — safe to parallelize.
- **Org discovery:** always automatic. `base.py` and `github.py`
  `discover_organizations_only` / `discover_repositories` derived org targets
  from `discover_organizations` (GitHub API → heuristic fallback). No way to
  inject a known org, and no way to skip API discovery.

## Change

- `keychecker/core/server_validator.py`
  - `validate_servers_streaming`: one task per provider, bounded by
    `asyncio.Semaphore(self.concurrency)`, yielded with `asyncio.as_completed`.
  - `discover_organizations_only` / `discover_repositories`: added `manual_orgs`
    and `discover_via_api` params, threaded to the provider.
- `keychecker/plugins/base.py`: `_merge_orgs` (dedupe, manual-first),
  `_org_discovery_method` (label `manual` / `manual+<method>`); both discovery
  methods merge manual + discovered, honor the skip switch, tolerate a missing
  username when a manual org is supplied, and emit `manual_organizations`.
- `keychecker/plugins/github.py`: same on the GitHub overrides; `discovery_method`
  reflects manual vs api/heuristic.
- `keychecker/cli.py`: `--org` (`action="append"`, comma-splittable via
  `_normalize_orgs`) and `--no-org-discovery`; guards (require `--discovery`;
  `--no-org-discovery` requires `--org`); threaded into discovery; help examples.
- `keychecker/utils/output.py`: show user-supplied orgs and manual method label.
- `ssh-keyrun.sh`: added `#!/usr/bin/env bash` shebang (see Notes).

## Commands

```
python3 -m venv /tmp/kcvenv
/tmp/kcvenv/bin/pip install cryptography asyncssh aiohttp tqdm pytest pytest-asyncio pytest-cov black flake8
/tmp/kcvenv/bin/python -m pytest tests/            # 60 passed
/tmp/kcvenv/bin/python -m pytest tests/ --cov=...  # new logic exercised
/tmp/kcvenv/bin/python -m flake8 <changed files>   # clean
/tmp/kcvenv/bin/python -m black --check keychecker/ tests/  # clean (after formatting 2 files)
aidc-scan                                          # clean
```

## Verification

- Full suite: 60 passed (was 26). New `tests/test_org_and_parallel.py` covers
  CLI parsing/guards, `_normalize_orgs`, `_merge_orgs`/`_org_discovery_method`,
  base + GitHub discovery with manual orgs and the skip switch, validator
  pass-through, output formatting, and concurrent validation (peak concurrency
  > 1, respects `--concurrency`, survives a provider raising).
- Coverage of changed modules: new lines exercised; residual gaps are
  abstract-method `pass` stubs, defensive `except` blocks, and pre-existing
  untested SSH/network code.
- `flake8`, `black --check`, and `aidc-scan` all clean.

## Notes

- Completion-order yielding is fine because the CLI collects results into a dict
  keyed by server name; ordering is irrelevant to the output.
- `aidc-scan` flagged shellcheck SC2148 on `ssh-keyrun.sh`, an untracked local
  helper script (not part of this change). Per the project's non-negotiable
  guardrail I did not skip it — the fix is a harmless shebang line, and the
  script already uses bash-only `[[ ]]`, so bash is correct.
- Environment quirk: the checked-in `.venv` is a macOS build (its `cryptography`
  `_rust.abi3.so` gives "invalid ELF header" on Linux) and the pinned uv
  `>=0.12.0` exceeds the container's 0.10.12, so `uv run` fails. Tests were run
  in a throwaway Linux venv at `/tmp/kcvenv`.
