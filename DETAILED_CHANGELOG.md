# Detailed Changelog

The long-form companion to `CHANGELOG.md`. Where `CHANGELOG.md` says *what*
changed in one line, this file records *why* and *how* — enough for a future
reader to audit, reproduce, or roll back any change without re-deriving it.

Add a new entry (newest first) for every meaningful change. Use the template
below; drop sections that genuinely don't apply.

---

## 2026-08-08 — Add `--validate all` and `--csv` summary output

**Summary:** Added a `--validate all` keyword that scans every supported
provider (all 19), and a `--csv FILE` option that appends a machine-readable
summary row per key so results can be collected across many keys.

**Why:** The tool validated only six core providers by default and offered no
way to scan every provider in one run; users had to enumerate them by hand.
There was also no structured output for batching — only human-readable text.
Requested: a CSV where each key id maps to `N` (no username found) or one or
more `provider:username` matches.

**What changed:**
- `keychecker/cli.py`
  - New module constants `ALL_PROVIDERS` (19), `DEFAULT_PROVIDERS` (6),
    `ALL_KEYWORD = "all"`, replacing the inline provider lists so the parser
    choices and the runtime default share one source of truth.
  - `--validate` now accepts `all`; in `run_analysis` an `all` in the list
    expands to `ALL_PROVIDERS`.
  - New `--csv FILE` argument and `_append_csv_row()` helper (uses the stdlib
    `csv` module so commas/quotes are escaped). After validation, a row is
    appended: `[key_path, sha256_fingerprint, *matches]` where matches are
    `provider:username` or a single `N`.
  - Repository discovery guard tightened to reject `--validate all` (discovery
    needs exactly one concrete provider).
- `keychecker/utils/output.py`
  - New `OutputFormatter.build_csv_row()` that builds the row, counting a
    provider only when it is reachable, authenticated, and resolved a username.
- `tests/test_csv_output.py`, `tests/test_cli.py` — new unit tests for the row
  builder, CSV append/escaping, `all` parsing/expansion, and the discovery
  guard.

**How / commands run:**
```
# functional check (network available in sandbox)
python -m keychecker test_keys/github_anantshri --validate all --csv /tmp/out.csv
# -> row: test_keys/github_anantshri,SHA256:M7vOmp...,github:anantshri
python -m keychecker test_keys/github_anantshri --no-validate --csv /tmp/out.csv
# -> appended row: ...,N

python -m pytest tests/ -q            # 22 passed
python -m flake8 keychecker/ tests/   # clean
python -m black --check keychecker/ tests/
aidc-scan                             # semgrep/gitleaks/shellcheck/bandit clean
```

**Errors encountered & resolution:** The checked-in `.venv` was built for
macOS and is unusable on the Linux container; `uv` is pinned to a version not
installed here and `pip` is guarded. Worked around by building a throwaway
venv (`python -m venv /tmp/kcvenv`) with `cryptography`+`pytest` for
verification only — no repo files changed. `black` reformatted the discovery
guard condition; re-ran tests and flake8 after formatting.

**Verification:** 22 tests pass (16 new); flake8 + black clean; `aidc-scan`
reports no findings; end-to-end runs produced the expected match, multi-key
append, and `N` rows.

**Notes / follow-ups:** The `all`-expansion and CSV-write branches live inside
the async `run_analysis` I/O path, which has no unit harness; they are covered
by end-to-end runs plus a mirror test of the expansion logic. CSV key id uses
both the file path and the SHA256 fingerprint (two leading columns) per the
requested format.

## YYYY-MM-DD — <short title>

**Summary:** One or two sentences on what changed and the user-facing effect.

**Why:** The problem, request, or constraint that prompted this. Link the issue
/ ticket / discussion if there is one.

**What changed:**
- File-by-file or component-by-component list of the edits.

**How / commands run:**
```
# exact commands executed, with the relevant output
```

**Errors encountered & resolution:** Anything that went wrong and how it was
fixed (or why it was left as-is).

**Verification:** How the change was proven to work — tests run, scanners,
manual checks, screenshots.

**Notes / follow-ups:** Design choices, trade-offs, and anything deferred.
