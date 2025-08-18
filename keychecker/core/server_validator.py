"""
Git server validation functionality for GitHub, GitLab, Bitbucket, etc.
"""

import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator

from ..plugins import (
    GitHubProvider,
    GitLabProvider,
    BitbucketProvider,
    CodebergProvider,
    GiteaProvider,
    HuggingFaceProvider,
)


class ServerValidator:
    """Validates SSH keys against Git hosting servers using plugins."""

    def __init__(
        self,
        timeout: int = 5,
        concurrency: int = 10,
        github_token: Optional[str] = None,
        show_progress: bool = True,
    ):
        self.timeout = timeout
        self.concurrency = concurrency

        # Initialize provider plugins
        self.providers = {
            "github": GitHubProvider(
                timeout=timeout,
                concurrency=concurrency,
                api_token=github_token,
                show_progress=show_progress,
            ),
            "gitlab": GitLabProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "bitbucket": BitbucketProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "codeberg": CodebergProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "gitea": GiteaProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "huggingface": HuggingFaceProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
        }

    def get_supported_servers(self) -> List[str]:
        """Get list of supported server names."""
        return list(self.providers.keys())

    def add_provider(self, name: str, provider: Any) -> None:
        """Add a custom provider plugin."""
        self.providers[name] = provider

    async def validate_servers(
        self, private_key_path: str, server_names: List[str]
    ) -> Dict[str, Any]:
        """
        Validate SSH key against multiple servers using plugins.

        Args:
            private_key_path: Path to SSH private key
            server_names: List of server names to validate against

        Returns:
            Dictionary with validation results for each server
        """
        results = {}

        # Create validation tasks using plugins
        tasks = []
        for server_name in server_names:
            if server_name.lower() in self.providers:
                provider = self.providers[server_name.lower()]
                task = provider.validate_key(private_key_path)
                tasks.append((server_name, task))

        # Execute validations concurrently
        for server_name, task in tasks:
            try:
                result = await task
                results[server_name] = result
            except Exception as e:
                results[server_name] = {
                    "reachable": False,
                    "error": str(e),
                    "username": None,
                    "authenticated": False,
                }

        return results

    async def validate_servers_streaming(
        self, private_key_path: str, server_names: List[str]
    ) -> AsyncGenerator[tuple[str, Dict[str, Any]], None]:
        """
        Validate SSH key against multiple servers using plugins,
        yielding results as they complete.

        Args:
            private_key_path: Path to SSH private key
            server_names: List of server names to validate against

        Yields:
            Tuple of (server_name, result) as each validation completes
        """
        # Execute validations sequentially to avoid terminal output interference
        for server_name in server_names:
            if server_name.lower() in self.providers:
                provider = self.providers[server_name.lower()]

                try:
                    result = await provider.validate_key(private_key_path)
                    yield server_name, result
                except Exception as e:
                    yield server_name, {
                        "reachable": False,
                        "error": str(e),
                        "username": None,
                        "authenticated": False,
                    }

    async def discover_organizations_only(
        self, private_key_path: str, server_name: str
    ) -> Dict[str, Any]:
        """
        Discover organizations for the key owner without testing repositories.

        Args:
            private_key_path: Path to SSH private key
            server_name: Name of the server to test against

        Returns:
            Dictionary with organization discovery results
        """
        if server_name.lower() not in self.providers:
            raise ValueError(
                f"Unsupported server: {server_name}. "
                f"Supported: {list(self.providers.keys())}"
            )

        provider = self.providers[server_name.lower()]

        # Get organization discovery info from the provider
        return await provider.discover_organizations_only(private_key_path)

    async def discover_repositories(
        self, private_key_path: str, server_name: str, wordlist_path: str
    ) -> Dict[str, Any]:
        """
        Discover private repositories accessible with the given key using plugins.

        Args:
            private_key_path: Path to SSH private key
            server_name: Server to discover repositories on
            wordlist_path: Path to wordlist file with candidate repository names

        Returns:
            Dictionary with repository discovery results
        """
        if server_name.lower() not in self.providers:
            raise ValueError(
                f"Unsupported server: {server_name}. "
                f"Supported: {list(self.providers.keys())}"
            )

        provider = self.providers[server_name.lower()]

        # Load wordlist
        try:
            with open(wordlist_path, "r") as f:
                repo_names = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            raise FileNotFoundError(f"Wordlist not found: {wordlist_path}")

        # Use the provider's repository discovery method
        return await provider.discover_repositories(private_key_path, repo_names)

    async def cleanup(self) -> None:
        """Clean up resources from all providers."""
        cleanup_tasks = []
        for provider in self.providers.values():
            if hasattr(provider, "cleanup"):
                cleanup_tasks.append(provider.cleanup())

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
