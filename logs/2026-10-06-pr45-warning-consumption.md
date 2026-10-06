# 2026-10-06 — PR #45 pull-in (cryptography warnings + encrypted PKCS#8)

## Symptom / goal

User: "see if https://github.com/cyfinoid/keychecker/pull/45/changes needs to
be pulled in." Evaluation then application (no commit; user commits/signs).

## Diagnosis

- PR #45 (fixes #11): consume `CryptographyDeprecationWarning` during key
  analysis and report it in output; detect `BEGIN ENCRYPTED PRIVATE KEY` as
  `pkcs8`. Author @ai-anant.
- `git apply --check` → applies cleanly (key_analyzer.py unchanged since the
  PR's base; output.py hunks don't collide with the uncommitted 08-15 work).
- Premise re-verified on the upgraded stack (cryptography 50.0.1):
  `CryptographyDeprecationWarning` still exists; DSA OpenSSH serialization
  still emits "SSH DSA key support is deprecated..."; loading emits nothing
  (the serialization site is the one that fires). Earlier "no warnings under
  `-W default`" observation in the dependency-upgrade log was an artifact of
  the suite never serializing a DSA key.
- Live bug confirmed: current analyzer reports `type: unknown` for an
  OpenSSL-encrypted PKCS#8 PEM.
- Verdict: pull in.

## Change

- Applied the PR diff verbatim (`keychecker/core/key_analyzer.py`,
  `keychecker/utils/output.py`, `tests/test_key_analyzer.py`).
- Scanner-gate adjustments (aidc-scan findings on the PR's test code):
  - DSA fixture: PR used `key_size=1024`; bandit B505 + semgrep
    insufficient-dsa-key-size flag it. First attempted 2048 — WRONG: SSH
    (ssh-dss) only supports 1024-bit DSA and cryptography's OpenSSH
    serializer raises "SSH supports only 1024 bit DSA keys", breaking the
    test (caught by the suite). Reverted to 1024 with documented inline
    suppressions (`# nosec B505` + `# nosemgrep: <rule-id>`) and a comment
    explaining the SSH constraint.
  - `"/tmp/fake_key"` label → `"fake_key"` (bandit B108 hardcoded-tmp).
  - Removed the stale `# nosec B324` on the MD5 fingerprint line in
    key_analyzer.py — bandit 1.9.x honors `usedforsecurity=False` and warns
    "nosec encountered (B324), but no failed test". Code unchanged.
- NOTE: this round was interrupted (user asked about PR #5) after the code
  edits but before docs; documentation completed later the same day — this
  file, CHANGELOG.md, and the DETAILED_CHANGELOG entry.

## Commands

```
git apply pr45.diff
pytest tests/ -q                          # 63 passed (60 + 3 new)
pytest tests/ -q -W default               # no leaked warnings
python -m keychecker.cli <dsa_key>        # ⚠️ deprecation line; stderr = 0 bytes
python -m keychecker.cli <enc_pkcs8_key>  # Type: pkcs8 (was unknown)
mypy keychecker/                          # clean
flake8/black (pre-ruff), aidc-scan        # clean
```

## Verification

- 63/63 tests; the DSA test asserts the warning is captured in the result
  and does NOT leak to the caller.
- End-to-end: DSA key prints the library ⚠️ with empty stderr; encrypted
  PKCS#8 reports `Type: pkcs8`, `Passphrase: YES`.
- mypy, ruff (post-adoption), aidc-scan all clean.

## Notes

- PR #45 can be closed once this lands.
- Interaction with the ruff adoption (same day): `ruff format` collapsed the
  MD5 `hashlib.md5(...)` call to one line — the removed `# nosec B324`
  comment is therefore absent from the collapsed form too; documented in the
  ruff DETAILED_CHANGELOG entry.
