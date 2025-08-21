"""
Hugging Face-specific provider plugin for KeyChecker.
"""

import asyncio
import re
from typing import Dict, Any, List, Optional

from .base import BaseGitProvider, ServerConfig


class HuggingFaceProvider(BaseGitProvider):
    """Hugging Face-specific provider implementation."""

    def __init__(
        self,
        timeout: int = 5,
        concurrency: int = 10,
        show_progress: bool = True,
    ):
        """Initialize Hugging Face provider."""
        config = ServerConfig(
            name="huggingface", hostname="hf.co", port=22, username="git"
        )
        super().__init__(config, timeout, concurrency, show_progress)

    async def validate_key(self, private_key_path: str) -> Dict[str, Any]:
        """
        Validate SSH key against Hugging Face and extract user information.

        Hugging Face returns specific banner format when authenticated.
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

        # Check for Hugging Face success patterns
        if "hi " in output_lower and "welcome to hugging face" in output_lower:
            # Extract username from "Hi username, welcome to Hugging Face"
            match = re.search(
                r"Hi (\w+), welcome to Hugging Face", output, re.IGNORECASE
            )
            if match:
                username = match.group(1)
                if username.lower() == "anonymous":
                    # Anonymous access - not actually authenticated
                    result["authenticated"] = False
                    result["error"] = "Anonymous access - key not authorized"
                else:
                    # Authenticated user
                    result["authenticated"] = True
                    result["username"] = username
            else:
                # Fallback for other welcome messages
                result["authenticated"] = True
        elif "successfully authenticated" in output_lower:
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
                f"Connection failed - "
                f'{output.split()[0] if output else "unknown error"}'
            )
        elif exit_code != 0:
            result["authenticated"] = False
            result["error"] = "Authentication failed - unknown error"

        return result

    async def identify_user(self, private_key_path: str) -> Optional[str]:
        """
        Identify the username associated with the private key.

        Args:
            private_key_path: Path to SSH private key

        Returns:
            Username if identified, None otherwise
        """
        result = await self.validate_key(private_key_path)
        return result.get("username")

    async def discover_organizations(
        self, private_key_path: str, username: str
    ) -> List[str]:
        """
        Discover organizations for the user.

        Args:
            private_key_path: Path to SSH private key
            username: Username to discover organizations for

        Returns:
            List of organization names
        """
        # For Hugging Face, we'll use a heuristic approach since there's no public API
        # for organization discovery
        organizations = []

        # Common organization patterns based on username
        common_patterns = [
            f"{username}-org",
            f"{username}org",
            username.replace("-", ""),
            username.replace("_", ""),
            f"{username}-team",
            f"{username}-dev",
            f"{username}-company",
        ]

        # Test if these organizations exist by trying common repository names
        sem = asyncio.Semaphore(5)  # Lower concurrency for org discovery

        async def test_organization(org_name: str) -> None:
            """Test if an organization exists and is accessible."""
            async with sem:
                # Try common repository names that organizations often have
                test_repos = [
                    ".github",
                    "README",
                    "docs",
                    "documentation",
                    "website",
                    "profile",
                ]

                for repo in test_repos:
                    try:
                        accessible = await self.test_repository_access(
                            private_key_path, org_name, repo
                        )
                        if accessible:
                            organizations.append(org_name)
                            break  # Found one accessible repo, org exists
                    except Exception:
                        continue  # nosec B112

        # Test organizations concurrently
        tasks = [test_organization(org) for org in common_patterns]
        await asyncio.gather(*tasks, return_exceptions=True)

        return organizations

    async def test_repository_access(
        self, private_key_path: str, owner: str, repo_name: str
    ) -> bool:
        """
        Test if a repository is accessible with the given key.

        Args:
            private_key_path: Path to SSH private key
            owner: Repository owner (user or organization)
            repo_name: Repository name

        Returns:
            True if repository is accessible, False otherwise
        """
        repo_url = f"git@{self.config.hostname}:{owner}/{repo_name}.git"
        return await self._run_git_ls_remote(private_key_path, repo_url)
