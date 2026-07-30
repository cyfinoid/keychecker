"""
CodeUP (Alibaba Cloud)-specific provider plugin for KeyChecker.

CodeUP is Alibaba Cloud's DevOps Git hosting platform (part of Yunxiao).
SSH host: codeup.aliyun.com (user: git)
Banner: "Welcome to Codeup, <username>!"
"""

from typing import Dict, Any, List, Optional
import re

from .base import BaseGitProvider, ServerConfig


class CodeupProvider(BaseGitProvider):
    """CodeUP provider implementation."""

    def __init__(
        self, timeout: int = 5, concurrency: int = 10, show_progress: bool = True
    ):
        """Initialize CodeUP provider."""
        config = ServerConfig(
            name="codeup", hostname="codeup.aliyun.com", port=22, username="git"
        )
        super().__init__(config, timeout, concurrency, show_progress)

    async def validate_key(self, private_key_path: str) -> Dict[str, Any]:
        """
        Validate SSH key against CodeUP and extract user information.

        CodeUP returns "Welcome to Codeup, <username>!" banner on auth success.
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

        # Check for CodeUP success patterns
        if "welcome to codeup" in output_lower:
            result["authenticated"] = True
            # Extract username from "Welcome to Codeup, <username>!"
            match = re.search(r"Welcome to Codeup, (.+?)(?:!|$)", output, re.IGNORECASE)
            if match:
                result["username"] = match.group(1).strip()
        elif "successfully authenticated" in output_lower:
            result["authenticated"] = True
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
        Identify the CodeUP username associated with the private key.
        """
        validation_result = await self.validate_key(private_key_path)
        return validation_result.get("username")

    async def discover_organizations(
        self, private_key_path: str, username: str
    ) -> List[str]:
        """
        Discover CodeUP organizations.

        TODO: Implement CodeUP organization discovery.
        """
        return []

    async def test_repository_access(
        self, private_key_path: str, owner: str, repo_name: str
    ) -> bool:
        """
        Test CodeUP repository access.
        """
        repo_url = f"git@codeup.aliyun.com:{owner}/{repo_name}.git"
        return await self._run_git_ls_remote(private_key_path, repo_url)
