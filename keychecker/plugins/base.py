"""
Base plugin interface for Git hosting providers.
"""

import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

try:
    from tqdm import tqdm

    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


@dataclass
class ServerConfig:
    """Configuration for a Git server."""

    name: str
    hostname: str
    port: int = 22
    username: str = "git"


class BaseGitProvider(ABC):
    """Abstract base class for Git hosting provider plugins."""

    def __init__(
        self,
        config: ServerConfig,
        timeout: int = 5,
        concurrency: int = 10,
        show_progress: bool = True,
    ):
        """
        Initialize the provider plugin.

        Args:
            config: Server configuration
            timeout: Connection timeout in seconds
            concurrency: Maximum concurrent connections
            show_progress: Whether to show progress bars
        """
        self.config = config
        self.timeout = timeout
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
        self.show_progress = show_progress and HAS_TQDM
        self._progress_enabled = show_progress and HAS_TQDM

    @abstractmethod
    async def validate_key(self, private_key_path: str) -> Dict[str, Any]:
        """
        Validate SSH key against the server and extract user information.

        Args:
            private_key_path: Path to SSH private key

        Returns:
            Dictionary with validation results including username if available
        """
        pass

    @abstractmethod
    async def identify_user(self, private_key_path: str) -> Optional[str]:
        """
        Identify the username associated with the private key.

        Args:
            private_key_path: Path to SSH private key

        Returns:
            Username if identified, None otherwise
        """
        pass

    @abstractmethod
    async def discover_organizations(
        self, private_key_path: str, username: str
    ) -> List[str]:
        """
        Discover organizations the user belongs to.

        Args:
            private_key_path: Path to SSH private key
            username: Username to discover organizations for

        Returns:
            List of organization names
        """
        pass

    async def discover_organizations_only(
        self, private_key_path: str
    ) -> Dict[str, Any]:
        """
        Discover organizations for the key owner without testing repositories.

        Args:
            private_key_path: Path to SSH private key

        Returns:
            Dictionary with organization discovery results
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
                    "error": "Could not identify username from key validation",
                }

            # Step 2: Discover organizations
            organizations = await self.discover_organizations(
                private_key_path, username
            )

            # Determine discovery method (this will be overridden by specific providers)
            discovery_method = "heuristic"  # Default

            return {
                "server": self.config.name,
                "username": username,
                "organizations": organizations,
                "discovery_method": discovery_method,
                "error": None,
            }

        except Exception as e:
            return {
                "server": self.config.name,
                "username": None,
                "organizations": [],
                "discovery_method": None,
                "error": str(e),
            }

    @abstractmethod
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
        pass

    async def discover_repositories(
        self, private_key_path: str, repo_names: List[str]
    ) -> Dict[str, Any]:
        """
        Discover accessible repositories using the provided wordlist.

        This is a default implementation that can be overridden by specific providers.

        Args:
            private_key_path: Path to SSH private key
            repo_names: List of repository names to test

        Returns:
            Dictionary with repository discovery results
        """
        results: Dict[str, Any] = {
            "server": self.config.name,
            "username": None,
            "organizations": [],
            "accessible_repositories": [],
            "total_attempts": 0,
            "successful_attempts": 0,
            "failed_attempts": 0,
            "errors": [],
        }
        # Type assertions to help mypy
        results["total_attempts"] = 0
        results["successful_attempts"] = 0
        results["failed_attempts"] = 0
        results["errors"] = []
        results["accessible_repositories"] = []

        try:
            # Step 1: Identify username
            username = await self.identify_user(private_key_path)
            results["username"] = username

            if not username:
                results["errors"].append(
                    "Could not identify username from key validation"
                )
                return results

            # Step 2: Discover organizations
            organizations = await self.discover_organizations(
                private_key_path, username
            )
            results["organizations"] = organizations

            # Step 3: Test repositories for each target separately
            targets = [username] + organizations

            async def test_target_repositories(
                owner: str, target_index: int
            ) -> List[Dict[str, Any]]:
                """Test repositories for a specific owner."""
                accessible_repos = []
                target_attempts = 0  # Local counter for this target

                # Create individual progress bar for this target
                pbar = None
                if self._progress_enabled:
                    pbar = tqdm(
                        total=len(repo_names),
                        desc=f"Testing {owner} repositories",
                        unit="repo",
                        leave=True,  # Keep the progress bar visible
                        dynamic_ncols=True,
                        ncols=80,
                    )

                try:
                    for repo_name in repo_names:
                        async with self.semaphore:
                            try:
                                accessible = await self.test_repository_access(
                                    private_key_path, owner, repo_name
                                )
                                if accessible:
                                    accessible_repos.append(
                                        {
                                            "owner": owner,
                                            "repository": repo_name,
                                            "full_name": f"{owner}/{repo_name}",
                                            "url": (
                                                f"git@{self.config.hostname}:"
                                                f"{owner}/{repo_name}.git"
                                            ),
                                            "type": (
                                                "user"
                                                if owner == username
                                                else "organization"
                                            ),
                                        }
                                    )
                                    results["successful_attempts"] += 1
                                else:
                                    results["failed_attempts"] += 1
                            except Exception as e:
                                results["failed_attempts"] += 1
                                results["errors"].append(
                                    f"Error testing {owner}/{repo_name}: {str(e)}"
                                )
                            finally:
                                results["total_attempts"] += 1
                                target_attempts += 1
                                if pbar:
                                    pbar.update(1)
                except Exception as e:
                    results["errors"].append(
                        f"Error testing {owner} repositories: {str(e)}"
                    )
                finally:
                    if pbar:
                        pbar.close()

                return accessible_repos

            # Test repositories for each target sequentially to show clear progress
            for target_index, owner in enumerate(targets):
                accessible_repos = await test_target_repositories(owner, target_index)
                results["accessible_repositories"].extend(accessible_repos)

        except Exception as e:
            results["errors"].append(f"Repository discovery failed: {str(e)}")

        return results

    async def _run_ssh_command(
        self, private_key_path: str, command: Optional[str] = None
    ) -> Tuple[int, str, str]:
        """
        Run SSH command against the server.

        Args:
            private_key_path: Path to SSH private key
            command: Optional command to run (None for connection test)

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        cmd = [
            "ssh",
            "-i",
            private_key_path,
            "-T",  # Disable pseudo-terminal allocation
            "-F",
            "/dev/null",  # Ignore all SSH config files
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            f"ConnectTimeout={self.timeout}",
            "-o",
            "BatchMode=yes",
            "-o",
            "LogLevel=ERROR",
            "-o",
            "IdentitiesOnly=yes",  # Only use the specified key
            "-o",
            "UseKeychain=no",  # Disable macOS keychain
            "-o",
            "PubkeyAuthentication=yes",
            "-o",
            "PasswordAuthentication=no",
            "-o",
            "KbdInteractiveAuthentication=no",
            "-o",
            "GSSAPIAuthentication=no",
            f"{self.config.username}@{self.config.hostname}",
        ]

        if self.config.port != 22:
            cmd.extend(["-p", str(self.config.port)])

        if command:
            cmd.append(command)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self.timeout * 2
            )

            return (
                proc.returncode or -1,
                stdout.decode("utf-8", errors="ignore"),
                stderr.decode("utf-8", errors="ignore"),
            )

        except asyncio.TimeoutError:
            return -1, "", f"Connection timeout after {self.timeout}s"
        except Exception as e:
            return -1, "", f"SSH command failed: {str(e)}"

    async def _run_git_ls_remote(self, private_key_path: str, repo_url: str) -> bool:
        """
        Test repository access using git ls-remote.

        Args:
            private_key_path: Path to SSH private key
            repo_url: Repository URL to test

        Returns:
            True if repository is accessible, False otherwise
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "ls-remote",
                repo_url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={
                    "GIT_SSH_COMMAND": (
                        f"ssh -i {private_key_path} -T -F /dev/null "
                        f"-o StrictHostKeyChecking=no -o ConnectTimeout={self.timeout} "
                        f"-o IdentitiesOnly=yes -o UseKeychain=no "
                        f"-o PubkeyAuthentication=yes -o PasswordAuthentication=no "
                        f"-o KbdInteractiveAuthentication=no -o GSSAPIAuthentication=no"
                    )
                },
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self.timeout * 2
            )

            return proc.returncode == 0

        except Exception:
            return False

    def _extract_username_from_banner(self, banner: str) -> Optional[str]:
        """
        Extract username from SSH banner using common patterns.

        Args:
            banner: SSH banner text

        Returns:
            Username if found, None otherwise
        """
        # Common username extraction patterns
        patterns = [
            r"Hi (\w+)!",
            r"Hello (\w+)",
            r"Welcome to .*, @?(\w+)!?",
            r"successfully authenticated.*?(\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, banner, re.IGNORECASE)
            if match:
                return match.group(1)

        return None
