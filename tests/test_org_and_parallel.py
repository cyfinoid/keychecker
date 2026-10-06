"""
Tests for the custom-org discovery options (--org / --no-org-discovery) and
for concurrent multi-provider validation (validate_servers_streaming).
"""

import asyncio

import pytest

from keychecker.cli import _normalize_orgs, create_parser, validate_args
from keychecker.core.server_validator import ServerValidator
from keychecker.plugins.base import BaseGitProvider, ServerConfig
from keychecker.plugins.github import GitHubProvider
from keychecker.utils.output import OutputFormatter


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #
class FakeProvider(BaseGitProvider):
    """Concrete provider with fully controllable discovery behaviour."""

    def __init__(self, username="alice", discovered=None, accessible=None, **kwargs):
        super().__init__(
            ServerConfig(name="fake", hostname="fake.example.com"),
            show_progress=False,
            **kwargs,
        )
        self._username = username
        self._discovered = discovered if discovered is not None else []
        # Set of "owner/repo" strings that should report as accessible.
        self._accessible = set(accessible or [])
        self.discover_called = False

    async def validate_key(self, private_key_path):
        return {"reachable": True, "username": self._username, "authenticated": True}

    async def identify_user(self, private_key_path):
        return self._username

    async def discover_organizations(self, private_key_path, username):
        self.discover_called = True
        return list(self._discovered)

    async def test_repository_access(self, private_key_path, owner, repo_name):
        return f"{owner}/{repo_name}" in self._accessible


# --------------------------------------------------------------------------- #
# CLI: --org / --no-org-discovery parsing and normalisation
# --------------------------------------------------------------------------- #
class TestOrgArgParsing:
    def test_org_repeatable(self):
        parser = create_parser()
        args = parser.parse_args(["key", "--org", "acme", "--org", "foo"])
        assert args.org == ["acme", "foo"]

    def test_no_org_discovery_flag(self):
        parser = create_parser()
        args = parser.parse_args(["key", "--org", "acme", "--no-org-discovery"])
        assert args.no_org_discovery is True

    def test_normalize_splits_commas_and_dedupes(self):
        # Repeatable + comma-separated + duplicates + whitespace all handled.
        assert _normalize_orgs(["acme", "foo,bar", " acme ", "baz,"]) == [
            "acme",
            "foo",
            "bar",
            "baz",
        ]

    def test_normalize_none_is_empty(self):
        assert _normalize_orgs(None) == []


class TestOrgArgGuards:
    def _base_argv(self, tmp_path, extra):
        key = tmp_path / "key"
        key.write_text("dummy")
        return [str(key)] + extra

    def test_org_requires_discovery(self, tmp_path):
        parser = create_parser()
        args = parser.parse_args(self._base_argv(tmp_path, ["--org", "acme"]))
        with pytest.raises(SystemExit) as exc:
            validate_args(args)
        assert exc.value.code == 1

    def test_no_org_discovery_requires_org(self, tmp_path):
        disco = tmp_path / "repos.txt"
        disco.write_text("r\n")
        parser = create_parser()
        args = parser.parse_args(
            self._base_argv(
                tmp_path,
                [
                    "--discovery",
                    str(disco),
                    "--validate",
                    "github",
                    "--no-org-discovery",
                ],
            )
        )
        with pytest.raises(SystemExit) as exc:
            validate_args(args)
        assert exc.value.code == 1

    def test_org_with_discovery_ok(self, tmp_path):
        disco = tmp_path / "repos.txt"
        disco.write_text("r\n")
        parser = create_parser()
        args = parser.parse_args(
            self._base_argv(
                tmp_path,
                ["--discovery", str(disco), "--validate", "github", "--org", "acme"],
            )
        )
        validate_args(args)  # should not raise
        assert args.org == ["acme"]


# --------------------------------------------------------------------------- #
# Base provider: org merging helpers
# --------------------------------------------------------------------------- #
class TestOrgMergeHelpers:
    def test_merge_dedupes_manual_first(self):
        assert BaseGitProvider._merge_orgs(["acme", "foo"], ["foo", "bar"]) == [
            "acme",
            "foo",
            "bar",
        ]

    def test_merge_drops_falsey(self):
        assert BaseGitProvider._merge_orgs(["", "acme"], ["", None]) == ["acme"]

    @pytest.mark.parametrize(
        "base,manual,via_api,expected",
        [
            ("heuristic", [], True, "heuristic"),
            ("api", [], True, "api"),
            (None, [], False, None),
            ("heuristic", ["acme"], True, "manual+heuristic"),
            ("api", ["acme"], False, "manual"),
            (None, ["acme"], False, "manual"),
        ],
    )
    def test_method_label(self, base, manual, via_api, expected):
        assert BaseGitProvider._org_discovery_method(base, manual, via_api) == expected


# --------------------------------------------------------------------------- #
# Base provider: discovery honours manual orgs and the skip switch
# --------------------------------------------------------------------------- #
class TestDiscoveryWithManualOrgs:
    def test_orgs_only_merges_manual_and_discovered(self):
        provider = FakeProvider(username="alice", discovered=["autoorg"])
        result = asyncio.run(
            provider.discover_organizations_only("k", manual_orgs=["acme"])
        )
        assert result["organizations"] == ["acme", "autoorg"]
        assert result["manual_organizations"] == ["acme"]
        assert result["discovery_method"] == "manual+heuristic"
        assert provider.discover_called is True

    def test_orgs_only_skip_api(self):
        provider = FakeProvider(username="alice", discovered=["autoorg"])
        result = asyncio.run(
            provider.discover_organizations_only(
                "k", manual_orgs=["acme"], discover_via_api=False
            )
        )
        assert result["organizations"] == ["acme"]
        assert result["discovery_method"] == "manual"
        assert provider.discover_called is False

    def test_orgs_only_manual_without_username(self):
        # No username but a manual org is still a usable target.
        provider = FakeProvider(username=None)
        result = asyncio.run(
            provider.discover_organizations_only(
                "k", manual_orgs=["acme"], discover_via_api=False
            )
        )
        assert result["error"] is None
        assert result["organizations"] == ["acme"]

    def test_repos_manual_org_becomes_target(self):
        provider = FakeProvider(
            username="alice", discovered=[], accessible={"acme/secret"}
        )
        result = asyncio.run(
            provider.discover_repositories(
                "k", ["secret"], manual_orgs=["acme"], discover_via_api=False
            )
        )
        full_names = [r["full_name"] for r in result["accessible_repositories"]]
        assert "acme/secret" in full_names
        assert result["organizations"] == ["acme"]
        assert provider.discover_called is False

    def test_repos_api_discovery_merges_with_manual(self):
        # discover_via_api=True path: discovered orgs merge behind manual ones.
        provider = FakeProvider(
            username="alice",
            discovered=["autoorg"],
            accessible={"alice/secret", "autoorg/secret", "acme/secret"},
        )
        result = asyncio.run(
            provider.discover_repositories(
                "k", ["secret"], manual_orgs=["acme"], discover_via_api=True
            )
        )
        assert provider.discover_called is True
        assert result["organizations"] == ["acme", "autoorg"]
        owners = {r["owner"] for r in result["accessible_repositories"]}
        assert owners == {"alice", "acme", "autoorg"}

    def test_repos_no_username_uses_manual_only(self):
        provider = FakeProvider(username=None, accessible={"acme/secret"})
        result = asyncio.run(
            provider.discover_repositories(
                "k", ["secret"], manual_orgs=["acme"], discover_via_api=False
            )
        )
        assert result["username"] is None
        assert not result["errors"]
        assert result["accessible_repositories"][0]["full_name"] == "acme/secret"


# --------------------------------------------------------------------------- #
# GitHub provider override honours manual orgs and the skip switch
# --------------------------------------------------------------------------- #
def _github(username="alice", api_orgs=None, accessible=None):
    """A GitHubProvider with all network/SSH I/O stubbed out."""
    provider = GitHubProvider(show_progress=False)
    api_orgs = api_orgs or []
    accessible = set(accessible or [])

    async def fake_identify(_path):
        return username

    async def fake_api(_username):
        return list(api_orgs)

    async def fake_access(_path, owner, repo):
        return f"{owner}/{repo}" in accessible

    provider.identify_user = fake_identify
    provider._get_user_organizations_via_api = fake_api
    provider.test_repository_access = fake_access
    return provider


class TestGitHubManualOrgs:
    def test_orgs_only_merges_api_and_manual(self):
        provider = _github(api_orgs=["autoorg"])
        result = asyncio.run(
            provider.discover_organizations_only("k", manual_orgs=["acme"])
        )
        assert result["organizations"] == ["acme", "autoorg"]
        assert result["discovery_method"] == "manual+api"

    def test_orgs_only_skip_api(self):
        provider = _github(api_orgs=["autoorg"])
        result = asyncio.run(
            provider.discover_organizations_only(
                "k", manual_orgs=["acme"], discover_via_api=False
            )
        )
        assert result["organizations"] == ["acme"]
        assert result["discovery_method"] == "manual"

    def test_repositories_skip_api_uses_manual_owner(self):
        provider = _github(api_orgs=["autoorg"], accessible={"acme/secret"})
        result = asyncio.run(
            provider.discover_repositories(
                "k", ["secret"], manual_orgs=["acme"], discover_via_api=False
            )
        )
        assert result["provider"] == "github"
        assert result["organizations"] == ["acme"]
        assert result["discovery_method"] == "manual"
        assert result["accessible_repositories"][0]["full_name"] == "acme/secret"

    def test_orgs_only_no_username_no_manual_errors(self):
        provider = _github(username=None)
        result = asyncio.run(provider.discover_organizations_only("k"))
        assert result["organizations"] == []
        assert result["error"]

    def test_orgs_only_heuristic_fallback(self):
        # API returns nothing -> heuristic runs and its result is used.
        provider = _github(api_orgs=[])

        async def fake_heuristic(_path, _username):
            return ["guessedorg"]

        provider._discover_organizations_heuristic = fake_heuristic
        result = asyncio.run(provider.discover_organizations_only("k"))
        assert result["organizations"] == ["guessedorg"]
        assert result["discovery_method"] == "heuristic"


# --------------------------------------------------------------------------- #
# ServerValidator threads manual-org options through to providers
# --------------------------------------------------------------------------- #
class TestValidatorPassThrough:
    def _validator(self, provider):
        validator = ServerValidator()
        validator.providers = {"fake": provider}
        return validator

    def test_orgs_only_pass_through(self):
        provider = FakeProvider(username="alice", discovered=["autoorg"])
        validator = self._validator(provider)
        result = asyncio.run(
            validator.discover_organizations_only(
                "k", "fake", manual_orgs=["acme"], discover_via_api=False
            )
        )
        assert result["organizations"] == ["acme"]
        assert provider.discover_called is False

    def test_repositories_pass_through(self, tmp_path):
        provider = FakeProvider(username="alice", accessible={"acme/secret"})
        validator = self._validator(provider)
        wordlist = tmp_path / "repos.txt"
        wordlist.write_text("secret\n")
        result = asyncio.run(
            validator.discover_repositories(
                "k", "fake", str(wordlist), manual_orgs=["acme"], discover_via_api=False
            )
        )
        assert result["organizations"] == ["acme"]
        assert result["accessible_repositories"][0]["full_name"] == "acme/secret"

    def test_unsupported_server_raises(self):
        validator = self._validator(FakeProvider())
        with pytest.raises(ValueError):
            asyncio.run(
                validator.discover_organizations_only("k", "nope", manual_orgs=["x"])
            )


# --------------------------------------------------------------------------- #
# Output formatting for manual / combined discovery methods
# --------------------------------------------------------------------------- #
class TestOrgDiscoveryOutput:
    def _fmt(self, info):
        return OutputFormatter(no_banner=True).format_organization_discovery(info)

    def test_manual_only_method(self):
        out = self._fmt(
            {
                "username": "alice",
                "organizations": ["acme"],
                "manual_organizations": ["acme"],
                "discovery_method": "manual",
                "error": None,
            }
        )
        assert "User-supplied organizations: acme" in out
        assert "API discovery off" in out

    def test_combined_method(self):
        out = self._fmt(
            {
                "username": "alice",
                "organizations": ["acme", "autoorg"],
                "manual_organizations": ["acme"],
                "discovery_method": "manual+api",
                "error": None,
            }
        )
        assert "user-supplied orgs + api" in out


# --------------------------------------------------------------------------- #
# Concurrent provider validation
# --------------------------------------------------------------------------- #
class SlowProvider(FakeProvider):
    """Records how many validations run at once."""

    def __init__(self, counter, name):
        super().__init__(username=name)
        self._counter = counter
        self._name = name

    async def validate_key(self, private_key_path):
        self._counter["active"] += 1
        self._counter["peak"] = max(self._counter["peak"], self._counter["active"])
        try:
            await asyncio.sleep(0.05)
        finally:
            self._counter["active"] -= 1
        return {"reachable": True, "username": self._name, "authenticated": True}


class TestParallelValidation:
    def test_streaming_runs_concurrently_and_returns_all(self):
        counter = {"active": 0, "peak": 0}
        validator = ServerValidator(concurrency=10)
        names = ["github", "gitlab", "bitbucket", "gitea"]
        validator.providers = {n: SlowProvider(counter, n) for n in names}

        async def collect():
            out = {}
            async for name, result in validator.validate_servers_streaming("k", names):
                out[name] = result
            return out

        results = asyncio.run(collect())
        assert set(results) == set(names)
        assert all(r["reachable"] for r in results.values())
        # If validation were sequential the peak concurrency would be 1.
        assert counter["peak"] > 1

    def test_streaming_respects_concurrency_bound(self):
        counter = {"active": 0, "peak": 0}
        validator = ServerValidator(concurrency=2)
        names = ["github", "gitlab", "bitbucket", "gitea"]
        validator.providers = {n: SlowProvider(counter, n) for n in names}

        async def drain():
            async for _ in validator.validate_servers_streaming("k", names):
                pass

        asyncio.run(drain())
        assert counter["peak"] <= 2

    def test_streaming_survives_provider_exception(self):
        class Boom(FakeProvider):
            async def validate_key(self, private_key_path):
                raise RuntimeError("kaboom")

        validator = ServerValidator(concurrency=5)
        validator.providers = {
            "github": FakeProvider(username="alice"),
            "gitlab": Boom(),
        }

        async def collect():
            out = {}
            async for name, result in validator.validate_servers_streaming(
                "k", ["github", "gitlab"]
            ):
                out[name] = result
            return out

        results = asyncio.run(collect())
        assert results["github"]["reachable"] is True
        assert results["gitlab"]["reachable"] is False
        assert "kaboom" in results["gitlab"]["error"]
