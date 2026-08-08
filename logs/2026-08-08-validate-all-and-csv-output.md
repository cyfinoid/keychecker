# 2026-08-08 — `--validate all` and CSV summary output

## Symptom / goal

Two feature requests:

1. The scanner validated only six core providers by default and could take an
   explicit provider list, but had no way to scan **all** providers in one run.
2. Need a CSV-style output: one key id per row, with `N` when no username is
   found, or `provider:username` entries when accounts are identified.

## Diagnosis

- Provider registry lives in `keychecker/core/server_validator.py` (19
  providers). The CLI (`keychecker/cli.py`) hard-coded two provider lists: the
  `--validate` `choices` (all 19) and a separate default list of 6 in
  `run_analysis`.
- Validation results flow through `validate_servers_streaming` as a dict of
  `{server: {reachable, authenticated, username, ...}}`. `username` is the field
  that marks "account identified".
- `OutputFormatter` (`keychecker/utils/output.py`) held all rendering; a CSV
  builder belonged there. No CLI/output unit tests existed (only
  `test_key_analyzer.py`).

## Change

- `keychecker/cli.py`
  - Added `ALL_PROVIDERS` (19), `DEFAULT_PROVIDERS` (6), `ALL_KEYWORD = "all"`
    constants; `--validate` `choices` and the runtime default now derive from
    them.
  - `--validate` accepts `all`; `run_analysis` expands `all` → `ALL_PROVIDERS`.
  - Added `--csv FILE` plus `_append_csv_row()` (stdlib `csv` for escaping).
    After validation a row `[key_path, sha256_fp, *matches]` is appended, where
    matches are `provider:username` or a single `N`.
  - Discovery guard now rejects `--validate all` (needs one concrete provider).
- `keychecker/utils/output.py`
  - Added `OutputFormatter.build_csv_row()`; counts a provider only when
    reachable + authenticated + has a username.
- Tests: `tests/test_csv_output.py`, `tests/test_cli.py` (16 new tests).
- Docs: `CHANGELOG.md`, `DETAILED_CHANGELOG.md`, `Readme.md`.

## Commands

```bash
# throwaway linux venv (checked-in .venv is macOS; uv pinned/absent; pip guarded)
python -m venv /tmp/kcvenv
/tmp/kcvenv/bin/python -m pip install cryptography pytest pytest-cov flake8 black

# functional (sandbox has network)
python -m keychecker test_keys/github_anantshri --validate all --csv /tmp/out.csv
#   -> test_keys/github_anantshri,SHA256:M7vOmp...,github:anantshri
python -m keychecker test_keys/github_anantshri --no-validate --csv /tmp/out.csv
#   -> appended: ...,N

python -m pytest tests/ -q          # 22 passed
python -m flake8 keychecker/ tests/ # clean
python -m black keychecker/cli.py   # reformatted discovery guard
aidc-scan                           # semgrep/gitleaks/shellcheck/bandit clean
```

## Verification

- 22 tests pass (16 new): row builder match/N/filter cases, CSV append +
  comma-escaping, `all` parse/expansion, discovery-guard rejections.
- flake8 + black clean; `aidc-scan` reports no findings.
- End-to-end runs produced the expected single-match, multi-key append, and
  `N` rows; `--validate all` scanned all 19 providers.

## Notes

- CSV key id uses **both** file path and SHA256 fingerprint as two leading
  columns (per the chosen format), so rows stay traceable to a file and to the
  crypto identity.
- The `all`-expansion and CSV-write branches sit inside the async
  `run_analysis` I/O path, which has no unit harness; covered by end-to-end
  runs plus a mirror unit test of the expansion logic.
- Environment friction: the committed `.venv` targets macOS and the pinned
  `uv`/guarded `pip` couldn't be used; verification ran in a throwaway venv
  with no repo files changed.
