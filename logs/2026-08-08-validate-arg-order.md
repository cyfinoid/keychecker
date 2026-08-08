# 2026-08-08 — `--validate all <file>` argument-order fix

## Symptom / goal

`uv run keychecker --validate all ./test_keys/github_anantshri` failed:

```
keychecker: error: argument --validate: invalid choice:
'./test_keys/github_anantshri' (choose from 'github', ...)
```

The user wanted the natural order `--validate all <file>` to just work.

## Diagnosis

`--validate` was declared with `nargs="*"` plus `choices=ALL_PROVIDERS + [ALL_KEYWORD]`
(`keychecker/cli.py`). With `nargs="*"`, argparse greedily consumes **every**
following token until the next `-`-prefixed flag — so `all` *and* the trailing
`key_file` path were both treated as provider choices, and the path failed the
`choices` check. This is unavoidable while `nargs="*"` precedes an optional
positional; it forced users to place the key file before `--validate`.

Reproduced with a minimal argparse parser: `--validate all <path>` → error;
`<path> --validate all` → parsed fine.

## Change

- `keychecker/cli.py`
  - Replaced `nargs="*" / choices=` on `--validate` with `type=_parse_validate`,
    a new helper that parses **one** comma-separated token (`github`,
    `github,gitlab`, `all`), strips/validates each provider against
    `ALL_PROVIDERS + [ALL_KEYWORD]`, and raises `argparse.ArgumentTypeError`
    with a helpful message on unknown providers. `args.validate` stays
    `list[str] | None`, so `all`-expansion and the discovery guard are unchanged.
  - Because `--validate` now consumes exactly one token, the `key_file`
    positional is free — natural order works.
  - Updated help text + epilog examples.
- `tests/test_cli.py`: added regression tests (`--validate all <file>` order,
  comma-separated multi-provider, invalid-provider rejection); updated the
  discovery-guard helper to comma-join providers instead of passing them as
  separate argv tokens.
- Docs: `Readme.md` (space- → comma-separated, added order-independent example),
  `CHANGELOG.md`, `DETAILED_CHANGELOG.md`.

### Diff (core)

```python
# before
parser.add_argument("--validate", nargs="*",
                    choices=ALL_PROVIDERS + [ALL_KEYWORD], help=...)

# after
def _parse_validate(value: str) -> List[str]:
    allowed = ALL_PROVIDERS + [ALL_KEYWORD]
    providers = [p.strip() for p in value.split(",") if p.strip()]
    if not providers:
        raise argparse.ArgumentTypeError("no providers specified")
    invalid = [p for p in providers if p not in allowed]
    if invalid:
        raise argparse.ArgumentTypeError(...)
    return providers

parser.add_argument("--validate", metavar="PROVIDERS",
                    type=_parse_validate, help=...)
```

## Commands

```bash
# checked-in .venv is macOS-only; local uv is 0.10.12 < pinned >=0.12.0.
# Built a throwaway linux venv with pip:
python3 -m venv /tmp/kc-venv
/tmp/kc-venv/bin/pip install asyncssh cryptography aiohttp rich pytest

PYTHONPATH=/workspace /tmp/kc-venv/bin/python -m pytest tests/test_cli.py -q
#   -> 13 passed

PYTHONPATH=/workspace /tmp/kc-venv/bin/python -m keychecker \
    --validate all ./test_keys/github_anantshri --no-progress
#   -> parses; scans all 19 providers; github: anantshri ✅
```

## Verification

- 13 CLI tests pass, including the three new ones.
- The exact previously-failing command now parses (`key_file` set,
  `validate=['all']`) and runs end-to-end, identifying `github: anantshri`.
- Invalid provider (`github,bogus`) rejected with a clear listing of choices.

## Notes

- Small breaking CLI change: multiple providers must now be comma-separated
  (`--validate github,gitlab`) rather than space-separated. That ambiguity is
  exactly what blocked the natural order, so it's the intended trade-off.
- Environment friction: committed `.venv` targets macOS; installed `uv`
  (0.10.12) is below the repo's pinned `>=0.12.0`, so `uv run` is unusable
  here. Verified in a throwaway pip venv with no repo files changed.
