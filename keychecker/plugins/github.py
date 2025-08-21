"""
GitHub-specific provider plugin for KeyChecker.
"""

import asyncio
import re
from typing import Dict, Any, List, Optional

from .base import BaseGitProvider, ServerConfig

try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


class GitHubProvider(BaseGitProvider):
    """GitHub-specific provider implementation."""

    def __init__(
        self,
        timeout: int = 5,
        concurrency: int = 10,
        api_token: Optional[str] = None,
        show_progress: bool = True,
    ):
        """Initialize GitHub provider."""
        config = ServerConfig(
            name="github", hostname="github.com", port=22, username="git"
        )
        super().__init__(config, timeout, concurrency, show_progress)
        self.api_token = api_token
        self.api_base_url = "https://api.github.com"
        self._session: Optional[aiohttp.ClientSession] = None

    async def validate_key(self, private_key_path: str) -> Dict[str, Any]:
        """
        Validate SSH key against GitHub and extract user information.

        GitHub returns specific banner format with username.
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

        # Check for GitHub success patterns
        if "hi " in output_lower and "successfully authenticated" in output_lower:
            result["authenticated"] = True
            # Extract username from "Hi username!"
            match = re.search(r"Hi (\w+)!", output, re.IGNORECASE)
            if match:
                result["username"] = match.group(1)
        elif "successfully authenticated" in output_lower:
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
        Identify the GitHub username associated with the private key.
        """
        validation_result = await self.validate_key(private_key_path)
        return validation_result.get("username")

    async def discover_organizations(
        self, private_key_path: str, username: str
    ) -> List[str]:
        """
        Discover GitHub organizations the user belongs to.

        Uses GitHub API if available, falls back to heuristic approach.
        """
        # Try API-based discovery first
        if HAS_AIOHTTP:
            try:
                api_orgs = await self._get_user_organizations_via_api(username)
                if api_orgs:
                    return api_orgs
            except Exception:
                # Fall back to heuristic approach if API fails
                pass  # nosec B110

        # Fallback: Heuristic approach
        return await self._discover_organizations_heuristic(private_key_path, username)

    async def _get_user_organizations_via_api(self, username: str) -> List[str]:
        """
        Get user's public organizations via GitHub API.

        Args:
            username: GitHub username

        Returns:
            List of organization names
        """
        if not HAS_AIOHTTP:
            return []

        url = f"{self.api_base_url}/users/{username}/orgs"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "KeyChecker/1.0.0",
        }

        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        try:
            if not self._session:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                self._session = aiohttp.ClientSession(timeout=timeout)

            async with self._session.get(url, headers=headers) as response:
                if response.status == 200:
                    orgs_data = await response.json()
                    return [org["login"] for org in orgs_data if "login" in org]
                elif response.status == 404:
                    # User not found or organizations not public
                    return []
                else:
                    # Other error, fall back to heuristic
                    return []

        except Exception:
            # Network error or other issue, fall back to heuristic
            return []

    async def _discover_organizations_heuristic(
        self, private_key_path: str, username: str
    ) -> List[str]:
        """
        Discover organizations using heuristic approach (fallback method).
        """
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
                        continue  # Try next repo  # nosec B112

        # Test common patterns concurrently
        tasks = [test_organization(org) for org in common_patterns]
        await asyncio.gather(*tasks, return_exceptions=True)

        return organizations

    async def discover_organizations_only(
        self, private_key_path: str
    ) -> Dict[str, Any]:
        """
        Discover organizations for the key owner without testing repositories.
        Override to include GitHub API-specific information.
        """
        try:
            # Step 1: Identify username
            username = await self.identify_user(private_key_path)
            if not username:
                return {
                    "server": self.config.name,
                    "username": None,
                    "organizations": [],
                    "discovery_method": None,
                    "api_available": HAS_AIOHTTP,
                    "api_token_provided": bool(self.api_token),
                    "error": "Could not identify username from key validation",
                }

            # Step 2: Discover organizations
            organizations = []
            discovery_method = "heuristic"
            api_available = HAS_AIOHTTP
            api_token_provided = bool(self.api_token)

            # Try API-based discovery first
            if HAS_AIOHTTP:
                try:
                    api_orgs = await self._get_user_organizations_via_api(username)
                    if api_orgs:
                        organizations = api_orgs
                        discovery_method = "api"
                except Exception:
                    # Fall back to heuristic approach if API fails
                    pass  # nosec B110

            # If API didn't work, try heuristic
            if not organizations:
                organizations = await self._discover_organizations_heuristic(
                    private_key_path, username
                )

            return {
                "server": self.config.name,
                "username": username,
                "organizations": organizations,
                "discovery_method": discovery_method,
                "api_available": api_available,
                "api_token_provided": api_token_provided,
                "error": None,
            }

        except Exception as e:
            return {
                "server": self.config.name,
                "username": None,
                "organizations": [],
                "discovery_method": None,
                "api_available": HAS_AIOHTTP,
                "api_token_provided": bool(self.api_token),
                "error": str(e),
            }

    async def test_repository_access(
        self, private_key_path: str, owner: str, repo_name: str
    ) -> bool:
        """
        Test if a GitHub repository is accessible with the given key.
        """
        repo_url = f"git@github.com:{owner}/{repo_name}.git"
        return await self._run_git_ls_remote(private_key_path, repo_url)

    async def discover_repositories(
        self, private_key_path: str, repo_names: List[str]
    ) -> Dict[str, Any]:
        """
        GitHub-specific repository discovery with enhanced features.
        """
        # Use the base implementation but add GitHub-specific enhancements
        results = await super().discover_repositories(private_key_path, repo_names)

        # Add GitHub-specific metadata
        results["provider"] = "github"
        results["api_available"] = HAS_AIOHTTP
        results["api_token_provided"] = self.api_token is not None
        results["discovery_method"] = (
            "api" if (HAS_AIOHTTP and results.get("organizations")) else "heuristic"
        )

        # GitHub-specific repository categorization
        if results["accessible_repositories"]:
            for repo in results["accessible_repositories"]:
                # Add GitHub-specific metadata
                repo["web_url"] = f"https://github.com/{repo['full_name']}"
                repo["clone_url_https"] = f"https://github.com/{repo['full_name']}.git"
                repo["clone_url_ssh"] = repo["url"]

        return results

    async def cleanup(self) -> None:
        """Clean up resources like HTTP sessions."""
        if self._session:
            await self._session.close()
            self._session = None

    async def get_user_public_repositories(self, username: str) -> List[str]:
        """
        Get list of user's public repositories (for future API integration).

        Currently returns empty list as we're not using GitHub API.
        In future versions, this could integrate with GitHub API.
        """
        # Placeholder for future GitHub API integration
        # This would require authentication tokens
        return []

    async def enhanced_organization_discovery(
        self, private_key_path: str, username: str
    ) -> Dict[str, Any]:
        """
        Enhanced organization discovery with more sophisticated techniques.

        This method could be expanded to use:
        1. GitHub API (when tokens are available)
        2. Social engineering patterns
        3. Common corporate naming conventions
        4. Domain-based organization guessing
        """
        orgs = await self.discover_organizations(private_key_path, username)

        return {
            "organizations": orgs,
            "discovery_method": "heuristic",
            "confidence": "medium" if orgs else "low",
            "suggestions": [
                f"Try common corporate patterns like: {username}-corp, {username}-inc",
                f"Check if {username} matches any known organization names",
                "Consider using GitHub API tokens for more accurate org discovery",
            ],
        }

    def get_repository_insights(self, repo_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide GitHub-specific insights about discovered repositories.
        """
        insights: Dict[str, Any] = {
            "potential_secrets": [],
            "security_concerns": [],
            "recommendations": [],
        }

        repo_name = repo_info.get("repository", "").lower()

        # Check for potentially sensitive repository names
        sensitive_patterns = [
            "secret",
            "private",
            "internal",
            "config",
            "env",
            "key",
            "cert",
            "password",
            "token",
            "credential",
            "auth",
            "vault",
            "backup",
        ]

        for pattern in sensitive_patterns:
            if pattern in repo_name:
                insights["potential_secrets"].append(
                    f"Repository name contains '{pattern}' - may contain sensitive data"
                )

        # Security recommendations
        if repo_info.get("type") == "organization":
            insights["security_concerns"].append(
                "Organization repository access detected"
            )
            insights["recommendations"].append("Review organization member permissions")

        insights["recommendations"].extend(
            [
                "Audit repository contents for secrets",
                "Check commit history for sensitive data",
                "Verify repository access permissions",
            ]
        )

        return insights
