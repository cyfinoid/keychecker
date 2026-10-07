# 2026-10-06 — pip-audit follow-up: multidict + urllib3 lock upgrades

## Symptom / goal

User: "run pip audit it seems more pip packages need update. see if we can
push them to latest version. if the package has a security issue then we can
bypass the 7 days cooldown."

## Diagnosis

- Audited the LOCKED set (not the ad-hoc venv): `uv export --frozen
  --all-extras --no-hashes --no-emit-project` → `pip-audit -r`.
- Findings: 4 vulnerabilities in 2 transitive packages:
  - multidict 6.7.1 — CVE-2026-104874 (items-view reference leak → remote
    memory exhaustion in aio-libs stack). Fix 6.9.1.
  - urllib3 2.7.0 — PYSEC-2026-4175 (proxy/target TLS config mixups),
    PYSEC-2026-4176 (Deflate streaming infinite loop), PYSEC-2026-4177
    (chunked-streaming chunk-size overread). Fix 2.8.0 (all three).
- Cooldown check: all fix releases PREDATE the lock's 2026-09-29 cutoff
  (multidict 6.9.1: 2026-09-21; urllib3 2.8.0: 2026-09-15) — no
  `exclude-newer` bypass needed. They were missed earlier because previous
  lock runs only upgraded explicitly named packages.
- Latest-check: multidict 7.0.0 (2026-09-26) exists but aiohttp 3.14.3 pins
  `multidict<7.0,>=4.5` → 6.9.1 is the latest resolvable. urllib3 2.8.0 is
  the latest overall.

## Change

- `uv.lock` only: `uv lock --exclude-newer 2026-09-29T00:00:00Z
  --upgrade-package multidict --upgrade-package urllib3` (uv 0.12.0);
  `[options]` P7D block restored verbatim after (hazard re-verified);
  revision 3 kept; delta = exactly two version entries.
- No pyproject/requirements/code changes (both are transitives).

## Commands

```
uv export --frozen --all-extras --no-hashes --no-emit-project -o locked-reqs.txt
pip-audit -r locked-reqs.txt     # 4 vulns/2 pkgs → after: "No known vulnerabilities found"
uv lock --exclude-newer 2026-09-29T00:00:00Z \
    --upgrade-package multidict --upgrade-package urllib3
# clean-copy verify (HEAD + new lock):
uv sync --all-extras && .venv/bin/python -m pytest tests/ -q   # 63 passed
.venv/bin/ruff check keychecker/ tests/                         # clean
```

## Verification

- pip-audit clean on the new locked set.
- 63/63 tests + ruff in a clean `uv sync --all-extras` env.
- Lock: revision 3, `[options]` block byte-identical to HEAD's, only
  multidict/urllib3 version entries changed.

## Notes

- Both user commits from between sessions observed (2769702, ad35783) —
  this session's delta builds on them; the working tree contained only
  uv.lock during this change.
- If a future security fix lands inside the 7-day window, the bypass is
  `--exclude-newer-package <pkg>=<early-date>` together with
  `--exclude-newer <cutoff>` (uv supports per-package overrides).
- Low in-repo reachability (documented in DETAILED_CHANGELOG) — upgraded so
  the shipped lock audits clean regardless.
- No commit made (user commits and signs separately).

## Fresh-eyes review round + record

Independent reviewer verified: lock delta = exactly two version entries
(three-way checked incl. residual diff after stripping wheel lines);
[options] block + revision 3 byte-identical; fix versions/dates confirmed
against PyPI+OSV (multidict 6.9.1 fix confirmed; aiohttp caps <7.0 even in
3.14.4); pip-audit independently re-run clean; .gitleaks.toml validated with
a scope probe (suppression confined to tests/test_key_analyzer.py;
test_keys/ true positives still flagged in --no-git mode); 63/63 tests pass
in the lock-exact venv; no commit (HEAD ad35783 unchanged).
Findings fixed: "22-char" → 24-char dummy body (comment + .gitleaks.toml);
"buffer overread" → "unbounded chunk-size buffering"; doc command filenames
aligned with the actual scratch artifacts.
Reviewer's incidental note, accepted as-is: other unflagged packages remain
below their latest pre-cutoff versions (e.g. certifi, idna) — consistent
with the targeted-upgrade policy; a full refresh was deliberately not done
(pip-audit clean is the completion criterion for this task).
