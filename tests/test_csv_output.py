"""
Tests for the CSV summary row builder (OutputFormatter.build_csv_row).
"""

from keychecker.utils.output import OutputFormatter


class TestBuildCsvRow:
    """Test cases for OutputFormatter.build_csv_row."""

    def setup_method(self):
        self.formatter = OutputFormatter(no_banner=True)

    def test_single_match(self):
        """A provider that resolves a username yields provider:username."""
        results = {
            "github": {"reachable": True, "authenticated": True, "username": "alice"},
        }
        row = self.formatter.build_csv_row("id_ed25519", "SHA256:abc", results)
        assert row == ["id_ed25519", "SHA256:abc", "github:alice"]

    def test_multiple_matches_preserve_order(self):
        """Every provider with a username is included, in iteration order."""
        results = {
            "github": {"reachable": True, "authenticated": True, "username": "alice"},
            "gitlab": {"reachable": True, "authenticated": True, "username": "alice"},
        }
        row = self.formatter.build_csv_row("id", "SHA256:xyz", results)
        assert row == ["id", "SHA256:xyz", "github:alice", "gitlab:alice"]

    def test_no_username_yields_n(self):
        """No identified account produces a single 'N' sentinel."""
        results = {
            "gitlab": {"reachable": True, "authenticated": False, "error": "denied"},
            "bitbucket": {"reachable": False, "error": "connection failed"},
        }
        row = self.formatter.build_csv_row("id", "SHA256:xyz", results)
        assert row == ["id", "SHA256:xyz", "N"]

    def test_empty_results_yields_n(self):
        """No validation performed at all still yields 'N'."""
        row = self.formatter.build_csv_row("id", "SHA256:xyz", {})
        assert row == ["id", "SHA256:xyz", "N"]

    def test_auth_success_without_username_is_not_a_match(self):
        """Auth success but no resolved username is not counted as a match."""
        results = {
            "azuredevops": {
                "reachable": True,
                "authenticated": True,
                "requires_repo_path": True,
            },
        }
        row = self.formatter.build_csv_row("id", "SHA256:xyz", results)
        assert row == ["id", "SHA256:xyz", "N"]

    def test_mixed_match_and_failures(self):
        """Only the resolving provider is emitted; failures are dropped."""
        results = {
            "github": {"reachable": True, "authenticated": True, "username": "bob"},
            "gitlab": {"reachable": True, "authenticated": False},
            "gitee": {"reachable": False, "error": "timeout"},
        }
        row = self.formatter.build_csv_row("id", "SHA256:xyz", results)
        assert row == ["id", "SHA256:xyz", "github:bob"]
