"""
GitLab-specific provider plugin for KeyChecker.

TODO: Implement GitLab-specific functionality.
"""

from typing import Dict, Any, List, Optional

from .base import BaseGitProvider, ServerConfig


class GitLabProvider(BaseGitProvider):
    """GitLab.com provider implementation."""

    def __init__(
        self, timeout: int = 5, concurrency: int = 10, show_progress: bool = True
    ):
        """Initialize GitLab provider."""
        config = ServerConfig(
            name="gitlab", hostname="gitlab.com", port=22, username="git"
        )
        super().__init__(config, timeout, concurrency, show_progress)

    async def validate_key(self, private_key_path: str) -> Dict[str, Any]:
        """
        Validate SSH key against GitLab and extract user information.

        GitLab returns specific banner format: "Welcome to GitLab, @username!"
        """
        exit_code, stdout, stderr = await self._run_ssh_command(private_key_path)

        # Combine stdout and stderr for analysis
        output = (stdout + stderr).strip()
        output_lower = output.lower()

        result = {
            "reachable": True,
            "authenticated": False,
            "username": None,
            "banner": output,
            "error": None,
        }

        # Check for GitLab success patterns
        if "welcome to gitlab," in output_lower and "@" in output:
            result["authenticated"] = True
            # Extract username from "Welcome to GitLab, @username!"
            import re

            match = re.search(r"Welcome to GitLab, @([^!]+)!", output, re.IGNORECASE)
            if match:
                result["username"] = match.group(1)
        elif "welcome to gitlab" in output_lower:
            result["authenticated"] = True
            # Try other patterns if the standard one doesn't work
            username = self._extract_username_from_banner(output)
            if username:
                result["username"] = username
        elif any(
            pattern in output_lower
            for pattern in [
                "permission denied (publickey)",
                "permission denied for user",
                "authentication failed",
                "publickey authentication failed",
            ]
        ):
            result["authenticated"] = False
            result["error"] = "Authentication failed - key not authorized"
        elif any(
            pattern in output_lower
            for pattern in [
                "connection refused",
                "connection timed out",
                "network is unreachable",
            ]
        ):
            result["reachable"] = False
            result["error"] = (
                f'Connection failed - {output.split()[0] if output else "unknown"}'
            )
        elif exit_code != 0:
            result["authenticated"] = False
            result["error"] = "Authentication failed - unknown error"

        return result

    async def identify_user(self, private_key_path: str) -> Optional[str]:
        """
        Identify the GitLab username associated with the private key.
        """
        validation_result = await self.validate_key(private_key_path)
        return validation_result.get("username")

    async def discover_organizations(
        self, private_key_path: str, username: str
    ) -> List[str]:
        """
        Discover GitLab groups/organizations.

        TODO: Implement GitLab group discovery.
        """
        # Placeholder - return empty list for now
        return []

    async def test_repository_access(
        self, private_key_path: str, owner: str, repo_name: str
    ) -> bool:
        """
        Test GitLab repository access.

        TODO: Implement GitLab-specific repository testing.
        """
        repo_url = f"git@gitlab.com:{owner}/{repo_name}.git"
        return await self._run_git_ls_remote(private_key_path, repo_url)


class GitLabSelfHostedProvider(BaseGitProvider):
    """Self-hosted GitLab provider implementation."""

    def __init__(
        self,
        hostname: str,
        port: int = 22,
        timeout: int = 5,
        concurrency: int = 10,
        show_progress: bool = True,
    ):
        """Initialize self-hosted GitLab provider."""
        config = ServerConfig(
            name=f"gitlab-{hostname}", hostname=hostname, port=port, username="git"
        )
        super().__init__(config, timeout, concurrency, show_progress)

    async def validate_key(self, private_key_path: str) -> Dict[str, Any]:
        """
        Validate SSH key against self-hosted GitLab.

        TODO: Implement self-hosted GitLab validation.
        """
        # Similar to GitLab.com but for self-hosted instances
        exit_code, stdout, stderr = await self._run_ssh_command(private_key_path)

        # Combine stdout and stderr for analysis
        output = (stdout + stderr).strip()
        output_lower = output.lower()

        result = {
            "reachable": True,
            "authenticated": False,
            "username": None,
            "banner": output,
            "error": None,
        }

        # Check for GitLab success patterns
        if "welcome to gitlab" in output_lower or "gitlab" in output_lower:
            result["authenticated"] = True
            # Try to extract username from banner
            result["username"] = self._extract_username_from_banner(output)
        elif any(
            pattern in output_lower
            for pattern in [
                "permission denied (publickey)",
                "permission denied for user",
                "authentication failed",
                "publickey authentication failed",
            ]
        ):
            result["authenticated"] = False
            result["error"] = "Authentication failed - key not authorized"
        elif any(
            pattern in output_lower
            for pattern in [
                "connection refused",
                "connection timed out",
                "network is unreachable",
            ]
        ):
            result["reachable"] = False
            result["error"] = (
                f'Connection failed - {output.split()[0] if output else "unknown"}'
            )
        elif exit_code != 0:
            result["authenticated"] = False
            result["error"] = "Authentication failed - unknown error"

        return result

    async def identify_user(self, private_key_path: str) -> Optional[str]:
        """TODO: Implement self-hosted GitLab username extraction."""
        return None

    async def discover_organizations(
        self, private_key_path: str, username: str
    ) -> List[str]:
        """TODO: Implement self-hosted GitLab group discovery."""
        return []

    async def test_repository_access(
        self, private_key_path: str, owner: str, repo_name: str
    ) -> bool:
        """Test self-hosted GitLab repository access."""
        repo_url = f"git@{self.config.hostname}:{owner}/{repo_name}.git"
        return await self._run_git_ls_remote(private_key_path, repo_url)
