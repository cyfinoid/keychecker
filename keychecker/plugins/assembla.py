"""
Assembla-specific provider plugin for KeyChecker.

Assembla is a source code hosting and collaboration platform.
SSH host: git.assembla.com (user: Git)
"""

from typing import Dict, Any, List, Optional
import re

from .base import BaseGitProvider, ServerConfig


class AssemblaProvider(BaseGitProvider):
    """Assembla provider implementation."""

    def __init__(
        self, timeout: int = 5, concurrency: int = 10, show_progress: bool = True
    ):
        """Initialize Assembla provider."""
        config = ServerConfig(
            name="assembla", hostname="git.assembla.com", port=22, username="Git"
        )
        super().__init__(config, timeout, concurrency, show_progress)

    async def validate_key(self, private_key_path: str) -> Dict[str, Any]:
        """
        Validate SSH key against Assembla and extract user information.

        Assembla returns specific banner format with username.
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

        # Check for Assembla success patterns
        if "successfully authenticated" in output_lower:
            result["authenticated"] = True
            # Try to extract username from banner
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
        Identify the Assembla username associated with the private key.
        """
        validation_result = await self.validate_key(private_key_path)
        return validation_result.get("username")

    async def discover_organizations(
        self, private_key_path: str, username: str
    ) -> List[str]:
        """
        Discover Assembla organizations.

        TODO: Implement Assembla organization discovery.
        """
        return []

    async def test_repository_access(
        self, private_key_path: str, owner: str, repo_name: str
    ) -> bool:
        """
        Test Assembla repository access.
        """
        repo_url = f"git@git.assembla.com:{owner}/{repo_name}.git"
        return await self._run_git_ls_remote(private_key_path, repo_url)
