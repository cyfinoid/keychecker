# 2026-08-08 — Fix CI build: flat-layout package discovery & license file

## Symptom

The GitHub Actions `lint` job failed at `uv sync --all-extras` while building
the editable install of the project:

```
× Failed to build `keychecker @ file:///home/runner/work/keychecker/keychecker`
╰─▶ Call to `setuptools.build_meta.build_editable` failed (exit status: 1)
    error: Multiple top-level packages discovered in a flat-layout:
      ['logs', 'keychecker'].
```

Accompanying warnings:
- `File '.../LICENSE.md' cannot be found`
- `project.license` as a TOML table is deprecated.

## Diagnosis

- The session-log convention introduced a top-level `logs/` directory. Without
  explicit package configuration, setuptools' automatic flat-layout discovery
  found both `keychecker/` and `logs/` as candidate top-level packages and
  refused to proceed (this is the fatal error).
- `pyproject.toml` declared `license = {file = "LICENSE.md"}`, but the repo
  ships `LICENSE` (GPLv3), so the referenced file did not exist. The table form
  is also deprecated in favour of an SPDX string.

## Change

`pyproject.toml`:

```diff
 [build-system]
-requires = ["setuptools>=45", "wheel"]
+requires = ["setuptools>=77", "wheel"]

-license = {file = "LICENSE.md"}
+license = "GPL-3.0-or-later"
+license-files = ["LICENSE"]

+[tool.setuptools.packages.find]
+include = ["keychecker*"]
+
 [tool.black]
```

## Commands

The repo `.venv` (mac path) and the system `uv` (0.10.12, below the pinned
`uv>=0.12`) were unusable for a direct build, so verification used a clean venv:

```
python -m venv /tmp/bv
/tmp/bv/bin/pip install "setuptools>=77" wheel build
/tmp/bv/bin/python -m build --wheel -n -o /tmp/kcout
```

## Verification

- Build succeeded: `Successfully built keychecker-1.1.0-py3-none-any.whl`.
- Wheel `top_level.txt` contains only `keychecker` (no `logs`).
- METADATA: `License-Expression: GPL-3.0-or-later`, `License-File: LICENSE`.
- `aidc-scan` → clean.

## Notes

- No runtime code changed; no new tests/coverage required.
- GPLv3 declared as `-or-later` to match conventional GPLv3 boilerplate; change
  to `GPL-3.0-only` if the project wants to pin to exactly v3.
