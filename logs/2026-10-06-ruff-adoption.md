# 2026-10-06 — Adopt ruff from PR #5 (evaluation + cherry-pick)

## Symptom / goal

User: "i m only interested in ruff not the uv cache. inspect if its usable we
then cherry pick it and attribute the directly if we cant attribute in code
commits." — i.e. evaluate the ruff half of PR #5 (author @prgyn8 /
PragyanTiwari), pull it in if viable, and credit the author in code/docs
since the work will land inside the maintainer's own signed commit rather
than a merge/cherry-pick of the PR's commits.

## Diagnosis

- PR #5 overall: `mergeable: False / dirty` vs main; written against
  setup-uv v6.5.0, uv 0.8.12, and `[tool.uv] dev-dependencies` (repo since
  moved to setup-uv v9, uv 0.12.x, PEP 735 dependency-groups). User declined
  the uv-cache half anyway.
- The ruff half, tested as-written (bare `ruff check`, no config, ruff
  0.16.10): **288 errors** (UP006/UP035/UP045/I001/BLE001/S110/RUF/... —
  ruff 0.16 ships much broader defaults than the old flake8 gate) and
  `ruff format --check` wants to reformat **20 files** (quote-style
  divergence from black 26). The PR predates these default expansions and
  was never valid against the current tree — not usable verbatim.
- Usable adaptation: a `[tool.ruff]` config that reproduces the existing
  flake8 gate exactly — `select = ["E","F","W"]`, line-length 88 (from
  `.flake8`), same excludes — verified "All checks passed!" on the current
  tree before adopting.

## Change

- `pyproject.toml`: `[tool.ruff]`/`[tool.ruff.lint]` parity config (with
  attribution comment to PR #5 / @prgyn8); `ruff>=0.16.9` added to
  `[project.optional-dependencies].dev` and `[dependency-groups].dev`;
  `black`/`flake8` removed from both; `[tool.black]` removed.
- `.flake8` deleted.
- `ci.yml` + `publish.yml` "Run linting" steps → `ruff check` +
  `ruff format --check` (attribution comment).
- `scripts/test.sh`, `scripts/setup-dev.sh` → ruff equivalents (incl. help
  text); keeps scripts consistent with CI, else `black .` per old help would
  produce code CI rejects.
- One-time `ruff format` (ruff 0.16.9): 20 files, purely mechanical
  quote-style normalization (spot-checked; e.g. `f'..{.. else "unknown"}'`
  → `f"..{.. else 'unknown'}"`).
- `uv.lock`: `uv lock --exclude-newer 2026-09-29T00:00:00Z` (uv 0.12.0);
  ruff 0.16.9 added (0.16.10 published 2026-10-01 → excluded by the lock's
  7-day policy); black/flake8 + transitives (click, mccabe, pycodestyle,
  pyflakes, pytokens) removed; `[options]` P7D block restored verbatim after
  the re-lock (known hazard — verified present afterwards); `revision = 3`
  preserved.
- `tests/test_key_analyzer.py`: DSA fixture back to `key_size=1024` with
  `# nosec B505` + `# nosemgrep:` and an explanatory comment — an earlier
  bandit-driven 2048-bit "fix" broke the test because SSH (ssh-dss) supports
  only 1024-bit DSA (cryptography `ssh.py` raises "SSH supports only 1024
  bit DSA keys"). Caught by the suite during this session's re-verification.

## Commands

```
ruff check --isolated --select E,F,W --line-length 88 keychecker/ tests/  # parity proof
ruff format keychecker/ tests/           # one-time; 20 files
ruff check keychecker/ tests/            # All checks passed
ruff format --check keychecker/ tests/   # clean
pytest tests/ -q                         # 63 passed
mypy keychecker/                         # clean
aidc-scan                                # clean
uv lock --exclude-newer 2026-09-29T00:00:00Z  # then restore [options] block
```

## Verification

- Parity: the new ruff gate selects exactly the rules flake8 ran (E/W/F at
  88 chars); old gate passed, new gate passes on the same tree.
- 63/63 tests; mypy clean; ruff check + format --check clean; aidc-scan
  clean (semgrep/bandit honor the documented DSA-1024 suppressions; no
  stale-nosec warnings).
- uv.lock: revision 3, `[options]` block byte-identical to HEAD, delta =
  +ruff 0.16.9, −black −flake8 −5 transitives.

## Notes

- Attribution handled in three places (no commit-chain attribution
  possible): `[tool.ruff]` comment in pyproject.toml, the CI lint-step
  comments, and the changelogs — all name @prgyn8 / PR #5.
- ruff 0.16's broader default rules (UP/I/BLE/S/RUF/...: 288 findings,
  202 autofixable) deliberately NOT enabled — separate maintainer decision;
  noted in the config comment and DETAILED_CHANGELOG.
- Recommendation recorded: close PR #5 (both halves now either declined or
  superseded).
- No commit made (user commits and signs separately).

## Fresh-eyes review round + record

Reviewer findings → dispositions (all fixed):
1. Undocumented `# nosec B324` removal inside the "mechanical reformat" file
   → it was the deliberate bandit stale-nosec cleanup from the PR #45 round,
   whose documentation had been interrupted; now documented in the PR #45
   entries (changelog + own session log) and referenced from the ruff entry.
2. `requirements.txt` still listed black/flake8 (third dependency listing),
   no ruff → fixed (ruff>=0.16.9 in, black/flake8 out).
3. `scripts/README.md` still instructed black/flake8 usage → fixed (both
   spots).
4. "identical rule outcome" overstated: ruff E501 exempts overlong trailing
   pragma comments (the combined DSA suppression line) → wording corrected in
   DETAILED_CHANGELOG Verification.
5. SBOMs were generated against the stale `.venv` (black/flake8 still
   listed) → regenerated from a fresh clean copy after `uv sync --all-extras`
   (ruff 0.16.9 present, black/flake8 + transitives gone; license check
   clean).
Also documented: `test.sh` format scope now matches CI lint scope
(keychecker/ tests/, examples/ outside — as it was for flake8).
Final state verified: ruff check + format --check clean, 63/63 tests, mypy
clean, aidc-scan clean, uv.lock `[options]` block intact, revision 3.
No commit made (user commits and signs separately).
