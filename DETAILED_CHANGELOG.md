# Detailed Changelog

The long-form companion to `CHANGELOG.md`. Where `CHANGELOG.md` says *what*
changed in one line, this file records *why* and *how* — enough for a future
reader to audit, reproduce, or roll back any change without re-deriving it.

Add a new entry (newest first) for every meaningful change. Use the template
below; drop sections that genuinely don't apply.

---

## 2026-10-06 — Adopt ruff (lint + format), replacing flake8 + black

**Summary:** Cherry-picked the ruff half of PR #5 ("uv Cache Integration",
@prgyn8/PragyanTiwari): CI and dev scripts now lint/format with ruff instead
of flake8 + black. The uv-cache half of that PR was declined (stale against
setup-uv v9 / uv 0.12 pins, see session log). Credit for the switch belongs
to @prgyn8; the diff here is an adaptation, not the PR's literal patch
(which predates ruff 0.16's expanded defaults and no longer applies).

**Why:**
- One fast tool replaces two; ruff check + ruff format cover the same gate.
- PR #5 as written is NOT mergeable: based on setup-uv v6.5.0 + uv 0.8.12 +
  `[tool.uv] dev-dependencies` (since migrated to PEP 735 dependency-groups),
  and its bare `ruff check` (no config) fails on this tree — ruff 0.16
  defaults now include UP/I/BLE/S/RUF/... (288 findings), far beyond the old
  flake8 gate.

**How:**
- `pyproject.toml`: new `[tool.ruff]`/`[tool.ruff.lint]` config mirroring the
  old gate — `select = ["E","F","W"]`, `line-length = 88`, `target-version =
  "py310"`, same excludes as `.flake8`. `ruff>=0.16.9` added to both dev
  groups; `black`/`flake8` removed from both; `[tool.black]` section removed;
  `.flake8` deleted (0.16.9 = newest release ≤ the lock's 7-day
  exclude-newer cutoff of 2026-09-29; 0.16.10 landed 2026-10-01).
- `.github/workflows/ci.yml` + `publish.yml`: "Run linting" steps now
  `uv run ruff check keychecker/ tests/` + `uv run ruff format --check
  keychecker/ tests/` (attribution comment included).
- `scripts/test.sh` + `scripts/setup-dev.sh`: black/flake8 invocations and
  help text swapped for the ruff equivalents. `scripts/README.md` and
  `requirements.txt` (the third dependency listing) updated to match.
  Note: `test.sh` previously ran `black --check .` over the whole repo; the
  new `ruff format --check keychecker/ tests/` matches the CI lint scope
  (`examples/demo.py` was never CI-linted and stays outside it).
- One-time `ruff format` (ruff 0.16.9): 20 files reformatted — 19 purely
  mechanical quote-style normalization (black 26 emits `f'...{x if y else
  "unknown"}'`, ruff format emits `f"...{x if y else 'unknown'}"`); the 20th
  (`key_analyzer.py`) additionally carries the deliberate `# nosec B324`
  comment removal documented in the PR #45 entry below (bandit 1.9.x honors
  `usedforsecurity=False` and warns about the stale nosec).
- `uv.lock`: regenerated with `uv lock --exclude-newer 2026-09-29T00:00:00Z`
  (uv 0.12.0); adds ruff 0.16.9, removes black/flake8 + transitives (click,
  mccabe, pycodestyle, pyflakes, pytokens); `[options]` P7D block restored
  verbatim; `revision = 3` kept.
- `tests/test_key_analyzer.py`: the DSA deprecation-warning fixture keeps
  `key_size=1024` — SSH (ssh-dss) supports only 1024-bit DSA and
  cryptography's OpenSSH serializer rejects other sizes (an earlier
  2048-bit "fix" for bandit/semgrep broke the test; reverted in favor of
  documented inline suppressions `# nosec B505` + `# nosemgrep:`).

**Commands:**
```
ruff format keychecker/ tests/          # one-time, 20 files
ruff check keychecker/ tests/           # All checks passed
ruff format --check keychecker/ tests/  # clean
pytest tests/ -q                        # 63 passed
mypy keychecker/                        # clean
aidc-scan                               # clean (suppressions honored)
uv lock --exclude-newer 2026-09-29T00:00:00Z   # + [options] block restored
```

**Verification:**
- ruff check + format --check clean with the parity config. Rule outcome
  matches the old flake8 gate for E/F/W, with one permissive divergence:
  ruff's E501 exempts overlong trailing pragma comments (e.g. the combined
  `# nosec B505 # nosemgrep: ...` suppression line in
  tests/test_key_analyzer.py), which flake8 would have flagged.
- 63/63 tests pass; mypy clean; aidc-scan clean (semgrep + bandit accept the
  documented DSA-1024 suppressions).
- Lock: revision 3, `[options]` block byte-identical, only ruff added and
  black/flake8 + transitives removed.

**Notes:**
- Attribution: since this lands as part of a squash commit rather than a
  cherry-picked commit chain, credit to @prgyn8 (PR #5) is recorded here, in
  CHANGELOG.md, and in comments at the `[tool.ruff]` config and the CI lint
  steps.
- Deliberately NOT enabling ruff 0.16's broader defaults (UP/I/BLE/S/RUF...:
  288 findings) — that's a separate decision for the maintainer; the config
  comment marks the intent.
- PR #5 should be closed rather than merged (its uv-cache half is stale; the
  ruff half is superseded by this change).

---

## 2026-10-06 — Consume & report cryptography deprecation warnings; detect encrypted PKCS#8

**Summary:** Pulled in PR #45 by @ai-anant (fixes #11), verified still
relevant on the upgraded stack (cryptography 50.0.1): deprecation warnings
emitted by the cryptography library during key analysis are captured and
reported as ⚠️ output lines instead of leaking to stderr, and encrypted
PKCS#8 keys (`BEGIN ENCRYPTED PRIVATE KEY`) are classified `pkcs8` instead
of `unknown`. Applied as `git apply` of the PR diff; three small test/code
adjustments were needed for this repo's scanner gates.

**Why:**
- Issue #11 asked for library warnings to be consumed and reported.
- Verified the premise survived the dependency upgrade: on cryptography
  50.0.1, DSA public-key serialization still emits
  `CryptographyDeprecationWarning: SSH DSA key support is deprecated and
  will be removed in a future release`, and the current analyzer reported
  `type: unknown` for OpenSSL-encrypted PKCS#8 keys.

**How:**
- `keychecker/core/key_analyzer.py` (PR #45):
  key loading and public-key serialization wrapped in
  `warnings.catch_warnings(record=True)`; `CryptographyDeprecationWarning`
  messages collected into a new `warnings` list on the analysis result
  (also present, empty, on the encrypted-key path). `_analyze_encrypted_key`
  gained the `BEGIN ENCRYPTED PRIVATE KEY` → `pkcs8` branch.
- `keychecker/utils/output.py`: both human-readable formatters print the
  result's `warnings` as ⚠️ lines.
- `tests/test_key_analyzer.py`: three new tests from the PR, adjusted for
  this repo's scanner gates:
  - DSA fixture kept at `key_size=1024` with `# nosec B505` +
    `# nosemgrep:` suppressions and an explanatory comment — SSH (ssh-dss)
    supports only 1024-bit DSA, so a larger key breaks the OpenSSH
    serializer (an initial 2048-bit scanner fix broke the test and was
    reverted).
  - Fake encrypted-key blob passed with path label `"fake_key"` instead of
    `"/tmp/fake_key"` (bandit B108).
- `keychecker/core/key_analyzer.py`: removed the stale `# nosec B324`
  trailing comment on the MD5 fingerprint line — bandit 1.9.x honors
  `usedforsecurity=False` and emits an "unused nosec" warning for it; the
  code itself is unchanged.

**Commands:**
```
git apply pr45.diff                     # applied cleanly onto HEAD state
pytest tests/ -q                        # 63 passed (3 new)
pytest tests/ -q -W default             # no warnings leak
python -m keychecker.cli <dsa_key>      # ⚠️ DSA deprecation shown; stderr empty
python -m keychecker.cli <enc_pkcs8>    # Type: pkcs8 (was: unknown)
mypy / ruff / aidc-scan                 # clean
```

**Verification:**
- 60 → 63 tests passing; the DSA test asserts the warning is captured in
  the result AND does not leak to the caller.
- Manual CLI runs: DSA key shows the library deprecation ⚠️ with 0 bytes on
  stderr; OpenSSL-style encrypted PKCS#8 key reports `Type: pkcs8`,
  `Passphrase: YES`.

**Notes:**
- PR #45 can be closed once this lands (superseded by this application).
- The PR's diff applied without conflicts; the only divergence from the
  literal PR patch is the three scanner-gate adjustments listed above.

---

## 2026-10-06 — Dependency upgrades superseding dependabot PRs #50–#55

**Summary:** Upgraded the six packages targeted by the open dependabot PRs to
the newest versions allowed by the repo's 7-day `exclude-newer-span` lock
policy (all at or above each PR's target, so every PR is superseded):
cryptography, aiohttp, tqdm, types-tqdm, pip (in `uv.lock`), and the pinned uv
installer (plus the CI uv version). No source-code changes.

**Why:**
- Six open dependabot PRs (#50–#55) each bump one package; applying them as a
  single coordinated upgrade avoids six sequential lock rewrites and CI runs.
- pip 26.1.2 (the version in `uv.lock`) is affected by published advisory
  PYSEC-2026-3721, fixed in 26.2 — upgrading closes a known vulnerability.
- `scripts/install.sh` still pinned `uv==0.11.32` as its fallback, below the
  repo's own `required-version = ">=0.12.0"` — stale and broken; CI pinned
  uv 0.12.0 while `requirements-uv.txt` moved to 0.12.23 — inconsistent.

**How:**
- `pyproject.toml` / `requirements.txt`: minimum specifiers raised to the
  locked versions — `cryptography>=50.0.1`, `aiohttp>=3.14.3`, `tqdm>=4.70.1`,
  `types-tqdm>=4.70.0` (base-version style, matching the previous `>=4.69.0`
  convention; both occurrence sites in `pyproject.toml`).
- `uv.lock`: regenerated surgically with uv 0.12.0 (the repo's minimum, to
  keep lock revision 3 exactly like dependabot's own PR diffs) via
  `uv lock --exclude-newer 2026-09-29T00:00:00Z --upgrade-package pip
  --upgrade-package aiohttp --upgrade-package cryptography --upgrade-package
  tqdm --upgrade-package types-tqdm`. The `--exclude-newer` date is the 7-day
  cutoff expressed by the lock's `[options] exclude-newer-span = "P7D"` policy
  (added by hand in 701a511; no uv 0.12.x CLI flag exists for the span, so the
  equivalent fixed date is used and the `[options]` block was restored
  verbatim afterwards, exactly as that commit did). Result: aiohttp 3.14.3,
  cryptography 50.0.1, pip 26.2.1, tqdm 4.70.1, types-tqdm 4.70.0.20260906,
  yarl 1.24.5 → 1.25.1 (aiohttp transitive), types-requests removed (newer
  types-tqdm no longer depends on it). Newer-than-cutoff releases
  deliberately NOT adopted: aiohttp 3.14.4 (published 2026-10-05),
  cryptography 50.0.2 (2026-09-30). No other packages touched; `revision = 3`
  preserved.
- `requirements-uv.txt`: `uv==0.12.23` with all 19 artifact hashes fetched
  from the PyPI JSON API (verified with `pip install --dry-run
  --require-hashes`; the first generated version lacked line-continuation
  backslashes, which pip silently ignores — caught and fixed).
- `scripts/install.sh` fallback pin `uv==0.11.32` → `uv==0.12.23`;
  `scripts/README.md` prerequisite line; `setup-uv` `version:` pins in
  `.github/workflows/ci.yml` (×4) and `publish.yml` (×4) `0.12.0` → `0.12.23`.
- `.github/workflows/publish.yml` (security fixes surfaced by
  aidc-scan/semgrep and fresh-eyes review once the file entered scope): the
  workflow-dispatch `version` input and the release `tag_name` context are now
  routed through `env:` variables (`VERSION_INPUT`, `RELEASE_TAG`) and
  referenced quoted in `run:` steps, instead of direct `${{ ... }}`
  interpolation (shell-injection vectors).
- `sbom/code.cdx.json` + `sbom/code.spdx.json`: regenerated by running
  `scripts/ci/aidc-sbom-all.sh` in a clean copy of the tree (the working
  tree's stale macOS `.venv` would pollute the catalog with old+new versions).

**Commands:**
```
# lock regeneration (uv 0.12.0 installed in a scratch venv; container has 0.10.12)
uv lock --exclude-newer 2026-09-29T00:00:00Z --upgrade-package pip \
    --upgrade-package aiohttp --upgrade-package cryptography \
    --upgrade-package tqdm --upgrade-package types-tqdm
# verification (scratch venvs + clean repo copy)
python -m pytest tests/ --cov=keychecker -q          # 60 passed
python -m pytest tests/ -q -W default                # no warnings (cryptography 50 clean)
python -m flake8 keychecker/ tests/ && python -m black --check keychecker/ tests/
python -m mypy keychecker/                           # clean
pip-audit                                            # no known vulnerabilities
uv sync --all-extras && pytest                       # under uv 0.12.0 AND 0.12.23: 60 passed
uv lock --check (under uv 0.12.23)                   # lock valid across pinned range
./scripts/ci/aidc-sbom-all.sh                        # SBOMs regenerated, license check clean
aidc-scan                                            # clean
```

**Verification:**
- Full suite (60 tests) passes against cryptography 50.0.1 / aiohttp 3.14.3 /
  tqdm 4.70.1 in a plain venv and in `uv sync --all-extras` environments
  built from the new lock under BOTH uv 0.12.0 and uv 0.12.23; no deprecation
  warnings under `-W default` (relevant to the still-open PR #45).
- flake8, black, mypy, pip-audit, and aidc-scan all clean.
- pip-audit confirmed the upgrade is security-relevant: a scratch venv's pip
  25.3 flagged PYSEC-2026-196/2875/2876/3721; with pip 26.2.1 the audit
  reports no known vulnerabilities.
- SBOM regeneration lists the new locked versions; the only dual-version
  entries are legitimate (stevedore 5.8.0/5.9.0 split by Python marker in the
  lock, and older action pins referenced only by `sbom.yml`); license check
  clean for GPL-3.0-or-later.

**Notes:**
- Dependabot PR mapping: #55 pip→26.2 (applied: 26.2.1), #54 aiohttp→3.14.3
  (3.14.3), #53 cryptography→50.0.0 (50.0.1), #52 tqdm→4.70.0 (4.70.1),
  #51 types-tqdm→4.70.0.20260805 (4.70.0.20260906), #50 uv→0.12.3 (0.12.23).
  All six can be closed once this lands.
- PR #46 ("pin uv installation to 0.12.0 across scripts", adds a UV_VERSION
  single-source variable and versioned astral.sh installer URLs) is NOT
  superseded: this change aligns the version pins but leaves the Linux/macOS
  curl-installer paths unversioned. #46 should be rebased onto 0.12.23.
- Lock revision intentionally kept at 3 (generated with uv 0.12.0) so any uv
  in the supported `>=0.12.0,<0.13.0` range can read it; verified with
  `uv sync` and `uv lock --check` under 0.12.23.
- Latent future issue (not addressed here): `required-version = ">=0.12.0,
  <0.13.0"` will make CI's `uv` commands fail once uv 0.13 ships and
  `setup-uv` installs it; the cap will need loosening at that point.

---

## 2026-08-15 — Parallel provider validation + custom-org discovery options

**Summary:** Two user-facing additions. (1) Multi-provider validation now runs
concurrently instead of serially, so `--validate all` (19 providers) completes
much faster. (2) New `--org` / `--no-org-discovery` flags let the user supply
organization name(s) for repository discovery instead of relying solely on
API/heuristic org discovery.

**Why:**
- Cross-provider validation was serial (`validate_servers_streaming` looped and
  `await`ed each provider one at a time — the older `validate_servers` did the
  same despite its "concurrently" docstring). With 19 providers each doing an
  SSH round-trip, that is needlessly slow. Progress bars are already disabled
  during validation (`cli.py`), so the original reason for serializing —
  terminal output interference — no longer applies.
- Org discovery was always automatic (GitHub API, then heuristic). Users who
  already know the target org (or whose org is private/not discoverable) had no
  way to point discovery at it.

**How:**
- `keychecker/core/server_validator.py`
  - `validate_servers_streaming` now creates one task per provider, bounds them
    with `asyncio.Semaphore(self.concurrency)`, and yields via
    `asyncio.as_completed` (completion order; the CLI collects into a dict so
    order is irrelevant). Per-provider exceptions are still caught and surfaced
    as unreachable results.
  - `discover_organizations_only` / `discover_repositories` gained
    `manual_orgs` and `discover_via_api` params, passed through to the provider.
- `keychecker/plugins/base.py`
  - Added `_merge_orgs` (dedupe, manual-first) and `_org_discovery_method`
    (labels the result `manual`, `manual+<method>`, or the bare method).
  - `discover_organizations_only` and `discover_repositories` merge manual orgs
    with discovered ones, skip API discovery when `discover_via_api=False`, and
    no longer hard-fail when the username can't be identified but a manual org
    was supplied (the manual org is still a valid target). Results now include
    a `manual_organizations` key.
- `keychecker/plugins/github.py` — same signature/behaviour changes on the
  GitHub-specific overrides; `discovery_method` reflects manual vs api/heuristic.
- `keychecker/cli.py` — added `--org` (`action="append"`, comma-splittable via
  `_normalize_orgs`) and `--no-org-discovery`; validation rejects the flags
  without `--discovery`, and `--no-org-discovery` without `--org`. Threaded both
  into the discovery calls. Added help examples.
- `keychecker/utils/output.py` — org-discovery output shows user-supplied orgs
  and the `manual` / `manual+<method>` discovery method.
- `ssh-keyrun.sh` — added a `#!/usr/bin/env bash` shebang to clear a shellcheck
  SC2148 finding surfaced by `aidc-scan` (untracked helper script; already uses
  bash-only `[[ ]]`).

**Commands:**
- `python -m pytest tests/` → 60 passed.
- Coverage over the changed modules (`--cov=keychecker.cli
  keychecker.core.server_validator keychecker.plugins.base
  keychecker.plugins.github keychecker.utils.output`): new logic exercised;
  remaining gaps are abstract-method stubs, defensive `except` handlers, and
  pre-existing untested SSH/network code.
- `flake8` + `black --check` clean; `aidc-scan` clean.

**Verification:** New `tests/test_org_and_parallel.py` covers: CLI parsing and
guards; `_normalize_orgs`; `_merge_orgs` / `_org_discovery_method`; base and
GitHub discovery with manual orgs and the skip switch; validator pass-through;
output formatting; and concurrent validation (asserts peak concurrency > 1,
respects the `--concurrency` bound, and survives a provider raising).

**Notes:** The repo's checked-in `.venv` is a macOS build (its `cryptography`
`_rust.abi3.so` fails with "invalid ELF header" on Linux), and the pinned uv
`>=0.12.0` is newer than the container's 0.10.12, so tests were run in a
throwaway Linux venv (`/tmp/kcvenv`) with the deps from `requirements.txt`.

---

## 2026-08-08 — Fix CI build: flat-layout package discovery and license file

**Summary:** The `lint` job failed at `uv sync --all-extras` while building the
editable install of `keychecker`. setuptools aborted with *"Multiple top-level
packages discovered in a flat-layout: ['logs', 'keychecker']"*, and separately
warned that `LICENSE.md` could not be found and that `project.license` as a TOML
table is deprecated.

**Why:** The session-log convention added a top-level `logs/` directory. With no
explicit package configuration, setuptools' automatic flat-layout discovery saw
both `keychecker/` and `logs/` as candidate top-level packages and refused to
guess. The `license = {file = "LICENSE.md"}` entry pointed at a file that does
not exist (the repo ships `LICENSE`), and the table form is deprecated in favor
of an SPDX string (setuptools>=77).

**How:** (`pyproject.toml`)
- Added `[tool.setuptools.packages.find]` with `include = ["keychecker*"]` so
  only the real package is discovered; `logs/`, `tests/`, `examples/`, etc. are
  ignored.
- Replaced `license = {file = "LICENSE.md"}` with the SPDX string
  `license = "GPL-3.0-or-later"` (matches the GPLv3 statement in `Readme.md`)
  plus `license-files = ["LICENSE"]`.
- Bumped the build requirement to `setuptools>=77` (required for the SPDX-string
  `license` form).

**Commands / verification:**
- Reproduced and verified the fix in a clean venv (repo `.venv` and system uv
  were stale/older than the pinned `uv>=0.12`):
  `python -m venv /tmp/bv && /tmp/bv/bin/pip install "setuptools>=77" wheel build`
  then `/tmp/bv/bin/python -m build --wheel -n` → `Successfully built
  keychecker-1.1.0-py3-none-any.whl`.
- Inspected the wheel: `top_level.txt` contains only `keychecker`; METADATA has
  `License-Expression: GPL-3.0-or-later` and `License-File: LICENSE`.
- `aidc-scan` → clean.

**Notes:** No runtime code changed, so no new tests/coverage apply. GPLv3 is
declared as `-or-later` to match the conventional GPLv3 boilerplate; switch to
`GPL-3.0-only` if the project intends to pin to exactly v3.

---

## 2026-08-08 — Make `--validate all <file>` work in any argument order

**Summary:** `keychecker --validate all ./test_keys/github_anantshri` failed
with `invalid choice: './test_keys/github_anantshri'`. Reworked `--validate`
to accept a single comma-separated value so it no longer swallows the trailing
`key_file` positional.

**Why:** `--validate` was defined with `nargs="*"` plus `choices=`, so argparse
greedily consumed every following token — including the key-file path — as a
provider name. With a trailing optional positional this is unavoidable while
`nargs="*"` is used, and it forced users to remember to put the key file
*before* `--validate`, which is not the natural order.

**How:**
- `keychecker/cli.py`: replaced `nargs="*" / choices=` on `--validate` with a
  custom `type=_parse_validate` that splits one comma-separated token (e.g.
  `github,gitlab`, or `all`), strips/validates each provider against
  `ALL_PROVIDERS + [ALL_KEYWORD]`, and raises `argparse.ArgumentTypeError`
  with a helpful message on an unknown provider. `args.validate` stays a
  `list[str] | None`, so all downstream logic (`all` expansion, discovery
  guard) is unchanged.
- Updated `--validate` help text, epilog examples, and the Readme usage
  (space-separated → comma-separated; added the `--validate all <file>`
  example).
- `tests/test_cli.py`: added regression tests for `--validate all <file>`
  ordering, comma-separated multi-provider parsing, and invalid-provider
  rejection; updated the discovery-guard helper to comma-join providers.

**Commands:**

```
PYTHONPATH=/workspace python -m pytest tests/test_cli.py -q          # 13 passed
PYTHONPATH=/workspace python -m keychecker --validate all ./test_keys/github_anantshri --no-progress
```

**Verification:** The previously-failing command now parses (`key_file` set,
`validate=['all']`) and runs end-to-end, scanning all 19 providers and
identifying `github: anantshri`. Invalid providers (`github,bogus`) are
rejected with a clear message listing valid choices.

**Notes:** This is a small breaking change to the CLI surface — multiple
providers must now be comma-separated (`--validate github,gitlab`) rather than
space-separated (`--validate github gitlab`). This is what makes the natural
argument order unambiguous.

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
