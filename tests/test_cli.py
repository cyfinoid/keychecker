"""
Tests for CLI argument handling: `--validate all` expansion, `--csv`, and the
repository-discovery guard against the 'all' keyword.
"""

import csv

import pytest

from keychecker import cli
from keychecker.cli import (
    ALL_PROVIDERS,
    ALL_KEYWORD,
    DEFAULT_PROVIDERS,
    _append_csv_row,
    create_parser,
    validate_args,
)


class TestValidateAllChoice:
    """The parser accepts 'all' and the constants stay consistent."""

    def test_all_is_a_valid_choice(self):
        parser = create_parser()
        args = parser.parse_args(["key", "--validate", "all"])
        assert args.validate == [ALL_KEYWORD]

    def test_validate_before_key_file(self):
        # Regression: `--validate all <file>` must not swallow the key path.
        parser = create_parser()
        args = parser.parse_args(["--validate", "all", "./test_keys/github"])
        assert args.validate == [ALL_KEYWORD]
        assert args.key_file == "./test_keys/github"

    def test_comma_separated_providers(self):
        parser = create_parser()
        args = parser.parse_args(["key", "--validate", "github,gitlab"])
        assert args.validate == ["github", "gitlab"]

    def test_invalid_provider_rejected(self):
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["key", "--validate", "notaprovider"])

    def test_empty_validate_value_rejected(self):
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["key", "--validate", ""])

    def test_all_providers_contains_defaults(self):
        # Every default provider must be a real provider in the full set.
        assert set(DEFAULT_PROVIDERS).issubset(set(ALL_PROVIDERS))

    def test_all_keyword_not_a_provider(self):
        assert ALL_KEYWORD not in ALL_PROVIDERS


class TestCsvArg:
    """--csv is parsed and rows are appended correctly."""

    def test_csv_flag_parsed(self):
        parser = create_parser()
        args = parser.parse_args(["key", "--csv", "out.csv"])
        assert args.csv == "out.csv"

    def test_append_csv_row_creates_and_appends(self, tmp_path):
        target = tmp_path / "results.csv"
        _append_csv_row(str(target), ["id_a", "SHA256:1", "github:alice"])
        _append_csv_row(str(target), ["id_b", "SHA256:2", "N"])

        with open(target, newline="") as f:
            rows = list(csv.reader(f))

        assert rows == [
            ["id_a", "SHA256:1", "github:alice"],
            ["id_b", "SHA256:2", "N"],
        ]

    def test_append_csv_row_quotes_commas(self, tmp_path):
        # Values containing commas round-trip via the csv module.
        target = tmp_path / "results.csv"
        _append_csv_row(str(target), ["a,b", "SHA256:1", "N"])

        with open(target, newline="") as f:
            rows = list(csv.reader(f))

        assert rows == [["a,b", "SHA256:1", "N"]]


class TestDiscoveryGuard:
    """Repository discovery requires exactly one concrete provider."""

    def _args(self, tmp_path, validate):
        key = tmp_path / "key"
        key.write_text("dummy")
        disco = tmp_path / "repos.txt"
        disco.write_text("repo1\n")
        parser = create_parser()
        argv = [str(key), "--discovery", str(disco)]
        if validate is not None:
            argv += ["--validate", ",".join(validate)]
        return parser.parse_args(argv)

    def test_discovery_rejects_all_keyword(self, tmp_path):
        args = self._args(tmp_path, [ALL_KEYWORD])
        with pytest.raises(SystemExit) as exc:
            validate_args(args)
        assert exc.value.code == 1

    def test_discovery_rejects_multiple_servers(self, tmp_path):
        args = self._args(tmp_path, ["github", "gitlab"])
        with pytest.raises(SystemExit) as exc:
            validate_args(args)
        assert exc.value.code == 1

    def test_discovery_accepts_single_concrete_server(self, tmp_path):
        args = self._args(tmp_path, ["github"])
        # Should not raise.
        validate_args(args)
        assert args.validate == ["github"]


class TestServerExpansion:
    """`all` expands to the full provider list at run time."""

    def test_expansion_logic_matches_constants(self):
        # Mirror the expansion branch in run_analysis without running I/O.
        validate = [ALL_KEYWORD]
        if ALL_KEYWORD in validate:
            servers = list(cli.ALL_PROVIDERS)
        else:
            servers = validate
        assert servers == ALL_PROVIDERS
        assert len(servers) == 19
