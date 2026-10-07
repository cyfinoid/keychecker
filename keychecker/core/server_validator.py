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
    AssemblaProvider,
    AzureDevOpsProvider,
    BolticProvider,
    DataOpsProvider,
    FramagitProvider,
    GitVerseProvider,
    LaunchpadProvider,
    NotABugProvider,
    SourceHutProvider,
    CodingProvider,
    CodeupProvider,
    GiteeProvider,
    GitFlicProvider,
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
            "dataops": DataOpsProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "assembla": AssemblaProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "boltic": BolticProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "sourcehut": SourceHutProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "notabug": NotABugProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "azuredevops": AzureDevOpsProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "framagit": FramagitProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "gitverse": GitVerseProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "launchpad": LaunchpadProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "coding": CodingProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "codeup": CodeupProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "gitee": GiteeProvider(
                timeout=timeout, concurrency=concurrency, show_progress=show_progress
            ),
            "gitflic": GitFlicProvider(
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
        Validate SSH key against multiple servers using plugins concurrently,
        yielding results as they complete.

        Validations run in parallel, bounded by ``self.concurrency`` so a large
        provider list (e.g. ``--validate all``) does not open an unbounded number
        of SSH connections at once. Results are yielded in completion order — the
        caller collects them into a dict keyed by server name, so ordering does
        not matter. Progress bars are disabled by the CLI during validation, so
        concurrent execution does not interleave terminal output.

        Args:
            private_key_path: Path to SSH private key
            server_names: List of server names to validate against

        Yields:
            Tuple of (server_name, result) as each validation completes
        """
        semaphore = asyncio.Semaphore(max(1, self.concurrency))

        async def _validate_one(name: str) -> tuple[str, Dict[str, Any]]:
            provider = self.providers[name.lower()]
            async with semaphore:
                try:
                    result = await provider.validate_key(private_key_path)
                except Exception as e:
                    result = {
                        "reachable": False,
                        "error": str(e),
                        "username": None,
                        "authenticated": False,
                    }
            return name, result

        tasks = [
            asyncio.create_task(_validate_one(server_name))
            for server_name in server_names
            if server_name.lower() in self.providers
        ]

        for completed in asyncio.as_completed(tasks):
            server_name, result = await completed
            yield server_name, result

    async def discover_organizations_only(
        self,
        private_key_path: str,
        server_name: str,
        manual_orgs: Optional[List[str]] = None,
        discover_via_api: bool = True,
    ) -> Dict[str, Any]:
        """
        Discover organizations for the key owner without testing repositories.

        Args:
            private_key_path: Path to SSH private key
            server_name: Name of the server to test against
            manual_orgs: Org names supplied by the user (merged with discovery)
            discover_via_api: When False, skip automatic org discovery

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
        return await provider.discover_organizations_only(
            private_key_path, manual_orgs, discover_via_api
        )

    async def discover_repositories(
        self,
        private_key_path: str,
        server_name: str,
        wordlist_path: str,
        manual_orgs: Optional[List[str]] = None,
        discover_via_api: bool = True,
    ) -> Dict[str, Any]:
        """
        Discover private repositories accessible with the given key using plugins.

        Args:
            private_key_path: Path to SSH private key
            server_name: Server to discover repositories on
            wordlist_path: Path to wordlist file with candidate repository names
            manual_orgs: Org names supplied by the user (merged with discovery)
            discover_via_api: When False, skip automatic org discovery

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
        return await provider.discover_repositories(
            private_key_path, repo_names, manual_orgs, discover_via_api
        )

    async def cleanup(self) -> None:
        """Clean up resources from all providers."""
        cleanup_tasks = []
        for provider in self.providers.values():
            if hasattr(provider, "cleanup"):
                cleanup_tasks.append(provider.cleanup())

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
