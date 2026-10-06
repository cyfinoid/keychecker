# 2026-10-06 — Dependency upgrades (supersede dependabot PRs #50–#55)

## Symptom / goal

Six open dependabot PRs, each bumping one package to a version that is already
outdated again:

| PR | Package | PR target | Applied | Latest (2026-10-06) |
|----|---------|-----------|---------|---------------------|
| #55 | pip (`uv.lock`) | 26.2 | 26.2.1 | 26.2.1 |
| #54 | aiohttp | 3.14.3 | 3.14.3 | 3.14.4 (2026-10-05, policy-excluded) |
| #53 | cryptography | 50.0.0 | 50.0.1 | 50.0.2 (2026-09-30, policy-excluded) |
| #52 | tqdm | 4.70.0 | 4.70.1 | 4.70.1 |
| #51 | types-tqdm | 4.70.0.20260805 | 4.70.0.20260906 | 4.70.0.20260906 |
| #50 | uv | 0.12.3 | 0.12.23 | 0.12.23 |

User asked to "upgrade packages" and handle the commit/sign themselves — no
commit made. Also fixed along the way (stale pins, not full PR scope): the
`uv==0.11.32` fallback in `scripts/install.sh` and CI's `setup-uv` 0.12.0.

## Diagnosis

- Locked/spec versions live in four places: `pyproject.toml` +
  `requirements.txt` (specifiers; repo convention: specifier == locked
  version), `uv.lock` (resolution; carries a hand-added `[options]`
  `exclude-newer-span = "P7D"` 7-day supply-chain policy from commit 701a511),
  and `requirements-uv.txt` (pinned uv + PyPI hashes for the Windows/pip
  path).
- pip 26.1.2 in `uv.lock` is affected by PYSEC-2026-3721 (fix 26.2) — the pip
  bump is a security fix, not just hygiene.
- Container uv is 0.10.12 < the repo's `>=0.12.0`, so scratch venvs with uv
  0.12.0 / 0.12.23 were used for all lock work (same environment quirk as the
  2026-08-08 and 2026-08-15 sessions).
- First attempt resolved to absolute latest (aiohttp 3.14.4, cryptography
  50.0.2) and silently dropped the lock's `[options]` policy block (uv warns
  "removal of global exclude newer" and re-resolves without it). The
  fresh-eyes review caught both. Final approach honors the policy: resolve
  with `--exclude-newer 2026-09-29T00:00:00Z` (the 7-day cutoff; no uv 0.12.x
  CLI flag exists for the span form) and restore the `[options]` block
  verbatim afterwards — the same hand-restore commit 701a511 itself used.

## Change

- `pyproject.toml` / `requirements.txt`: `cryptography>=50.0.1`,
  `aiohttp>=3.14.3`, `tqdm>=4.70.1`, `types-tqdm>=4.70.0` (both occurrence
  sites: optional-dependencies and dependency-groups).
- `uv.lock`: surgical `uv lock --exclude-newer 2026-09-29T00:00:00Z
  --upgrade-package …` (five named packages) — aiohttp 3.14.3, cryptography
  50.0.1, pip 26.2.1, tqdm 4.70.1, types-tqdm 4.70.0.20260906, transitive yarl
  1.25.1; types-requests dropped (new types-tqdm no longer needs it);
  `[options]` P7D block restored byte-identical; `revision = 3` preserved
  (generated with uv 0.12.0; uv 0.12.23 rewrites the lock at revision 5,
  which older uv cannot read — dependabot's own PR diffs keep revision 3).
  HAZARD: any later `uv lock`-writing invocation silently drops the
  `[options]` block again — it happened once mid-session (caught by the
  second fresh-eyes review) and had to be re-restored. Re-check the block
  after any uv command and before committing.
- `requirements-uv.txt`: `uv==0.12.23` + 19 artifact hashes from the PyPI
  JSON API, header "Last updated" bumped.
- `scripts/install.sh` fallback pin `uv==0.11.32` → `uv==0.12.23`;
  `scripts/README.md` prerequisite line; `setup-uv` `version:` in
  `.github/workflows/ci.yml` (×4) and `publish.yml` (×4) → `0.12.23`.
- `sbom/code.cdx.json` / `sbom/code.spdx.json`: regenerated via
  `scripts/ci/aidc-sbom-all.sh` in a clean copy of the tree (scanning the
  worktree directly catalogs the stale macOS `.venv`'s old versions alongside
  the new lock — mixed-version SBOM; flagged by fresh-eyes review).
  `sbom/license-report.json` left as tracked (CI runs it in `fail` mode; the
  local script default `warn` output was discarded).
- `.github/workflows/publish.yml`: semgrep (via aidc-scan, which scoped the
  file in after the uv-pin edit) flagged direct
  `${{ github.event.inputs.version }}` use in two `run:` steps as
  shell-injection. Fixed by routing the input through
  `env: VERSION_INPUT` and quoting it (`"$VERSION_INPUT"`). The second
  fresh-eyes review flagged two more same-class sites using
  `${{ github.event.release.tag_name }}` — fixed identically via
  `env: RELEASE_TAG`. Pre-existing findings, fixed rather than skipped per
  the repo's guardrail.
- No source-code changes.

## Commands

```
python3 -m venv /tmp/.../uv120 && pip install uv==0.12.0     # lock writer
python3 -m venv /tmp/.../uvbin && pip install uv==0.12.23    # cross-version check
uv lock --exclude-newer 2026-09-29T00:00:00Z --upgrade-package pip \
    --upgrade-package aiohttp --upgrade-package cryptography \
    --upgrade-package tqdm --upgrade-package types-tqdm
# [options] exclude-newer-span block restored verbatim afterwards (701a511 style)
python -m pytest tests/ --cov=keychecker -q          # 60 passed
python -m pytest tests/ -q -W default                # no warnings surfaced
python -m flake8 keychecker/ tests/                  # clean
python -m black --check keychecker/ tests/           # clean
python -m mypy keychecker/                           # clean
pip-audit                                            # no known vulnerabilities
# clean repo copy (no macOS .venv), under BOTH uv 0.12.0 and 0.12.23:
uv sync --all-extras && .venv/bin/python -m pytest tests/ -q   # 60 passed each
uv lock --check                                      # OK under 0.12.23
./scripts/ci/aidc-sbom-all.sh                        # SBOMs + license check clean
aidc-scan                                            # clean
```

## Verification

- 60/60 tests pass against the upgraded stack in a plain venv and in
  `uv sync --all-extras` environments built from the new lock under uv 0.12.0
  AND uv 0.12.23 (lock readable and installable across the whole supported
  range). Coverage of the change itself is trivially satisfied (zero source
  lines changed).
- `pytest -W default` shows no deprecation warnings on cryptography 50
  (relevant context for still-open PR #45).
- pip-audit: scratch venv's pip 25.3 flagged PYSEC-2026-196/2875/2876/3721;
  with pip 26.2.1 the audit is clean — confirms the pip bump's security value.
- `pip install --dry-run --require-hashes -r requirements-uv.txt` passes
  (first generation lacked continuation backslashes — pip silently ignored
  the orphaned hash lines and failed on a real mismatch; fixed and
  re-verified).
- SBOMs regenerated from a clean tree list the new locked versions; the only
  dual-version entries are legitimate (stevedore split by Python marker in
  the lock, older action pins referenced only by `sbom.yml`); license check
  clean for GPL-3.0-or-later.
- aidc-scan clean (semgrep, gitleaks, shellcheck, bandit, vet, license-check).

## Notes

- Fresh-eyes review findings and dispositions:
  - Round 1: (1) lock `[options]` policy block dropped → fixed (policy
    honored, block restored); (2) "folded in PR #46's intent" was overstated →
    corrected (this change aligns version pins only; #46's UV_VERSION
    single-source variable and versioned astral.sh installer URLs remain
    unimplemented — rebase #46 onto 0.12.23); (3) SBOMs regenerated by
    aidc-scan were mixed-version and undocumented → regenerated cleanly via
    the repo's own script and documented.
  - Round 2: (4) the restored `[options]` block had been stripped again by a
    later uv-writing step → re-restored and re-verified (see HAZARD above);
    (5) "SBOM lists exactly one version per package" overstated (legitimate
    dual-marker stevedore + sbom.yml-only action pins) → wording softened;
    (6) two more `${{ github.event.release.tag_name }}` injection sites in
    publish.yml → fixed via `env: RELEASE_TAG`.
- uv 0.12.x cannot parse `exclude-newer-span` from CLI or pyproject — only a
  fixed `--exclude-newer <date>` exists — so the span policy can only be
  applied by translating it to a date at lock time, then restoring the span
  block by hand. Anyone re-locking should do the same (or the block's meaning
  is silently dropped, with only a warning).
- Latent future issue (flagged, not addressed): `required-version =
  ">=0.12.0,<0.13.0"` will break CI once uv 0.13 ships and `setup-uv`
  installs it; the cap needs loosening then. Same for the unversioned
  astral.sh installer URLs in `scripts/install.sh` (PR #46's remaining scope).
- Dependabot PRs #50–#55 can be closed once this lands; #46 needs a rebase;
  #5 (uv cache) and #45 (cryptography deprecation warnings) unaffected.
- Worktree already contained uncommitted PR #48 work; this change is additive
  on top and was not committed, per the user's instruction.

## Review record

Two fresh-eyes subagent review rounds (diff + task + AGENTS.md only, no
implementation reasoning handed over). Round 1: 3 real findings — all fixed.
Round 2: 1 blocker (options block stripped again post-restore) + 2 minor
(overstated SBOM claim; two more tag_name injection sites) — all fixed.
Deferrals (flagged, not fixed): `required-version` `<0.13.0` cap will break
CI when uv 0.13 ships; astral.sh installer URLs in `scripts/install.sh` remain
unversioned (PR #46 scope). aidc-scan clean on final state; lock `[options]`
block verified present after the final scan; 60/60 tests green. No commit
made (user commits and signs separately).

## Incident (disclosed)

`ssh-keyrun.sh` — an untracked 695-byte bash helper from the 2026-08-15
session (see that log's Notes) — was present at session start but is now
missing from the worktree; no command in this session's recorded transcript
deletes it, so it was most likely removed as a side effect of one of the
automated passes (aidc-scan or a review subagent). It is not in git
(untracked) and no copy survives under /tmp. Not reconstructed/fabricated.
If the 2026-08-15 session's environment still has it, restore it before
committing; otherwise recreate from that session's description.
