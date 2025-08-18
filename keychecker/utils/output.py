"""
Output formatting utilities for human-readable output.
"""

import sys
from typing import Dict, Any, Optional, List


class OutputFormatter:
    """Handles output formatting in different modes."""

    def __init__(self, no_banner: bool = False, verbose: bool = False):
        self.no_banner = no_banner
        self.verbose = verbose

    def print_banner(self) -> None:
        """Print application banner."""
        if self.no_banner:
            return

        banner = """
🔑 KeyChecker - SSH Key Analysis Tool
=====================================
🎓 Learn cybersecurity: https://cyfinoid.com/trainings/#upcoming-trainings
"""
        print(banner)

    def format_analysis_result(
        self,
        result: Dict[str, Any],
        validation_results: Optional[Dict[str, Any]] = None,
        repo_discovery_results: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format the complete analysis result."""
        return self._format_human_readable(
            result, validation_results, repo_discovery_results
        )

    def format_key_analysis(self, result: Dict[str, Any]) -> str:
        """Format only the key analysis results."""
        return self._format_key_analysis_human_readable(result)

    def format_validation_results(self, validation_results: Dict[str, Any]) -> str:
        """Format only the validation results."""
        return self._format_validation_results_human_readable(validation_results)

    def format_single_validation_result(
        self, server_name: str, result: Dict[str, Any]
    ) -> str:
        """Format a single validation result."""
        return self._format_single_validation_result_human_readable(server_name, result)

    def format_organization_discovery(
        self, org_discovery_results: Dict[str, Any]
    ) -> str:
        """Format only the organization discovery results."""
        return self._format_organization_discovery_human_readable(org_discovery_results)

    def format_repository_discovery_results(
        self, repo_discovery_results: Dict[str, Any]
    ) -> str:
        """Format only the repository discovery results."""
        return self._format_repository_discovery_human_readable(repo_discovery_results)

    def _format_human_readable(
        self,
        result: Dict[str, Any],
        validation_results: Optional[Dict[str, Any]] = None,
        repo_discovery_results: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format output in human-readable format."""
        lines = []

        # Key information
        lines.append(f"Key: {result['input']}")
        lines.append(f"Type: {result['key']['type']}")

        if result["key"]["bits"]:
            lines.append(f"Bits: {result['key']['bits']}")

        if result["key"].get("curve"):
            lines.append(f"Curve: {result['key']['curve']}")

        passphrase_status = "YES" if result["key"]["passphrase"] else "NO"
        lines.append(f"Passphrase: {passphrase_status}")

        # Public key info
        if result["public_key"]["key_string"]:
            pub_key = result["public_key"]["key_string"]
            if len(pub_key) > 80:
                pub_key = pub_key[:77] + "..."
            lines.append(f"Public: {pub_key}")

        if result["public_key"]["comment"]:
            lines.append(f"Comment: {result['public_key']['comment']}")

        # Fingerprints
        if result["public_key"]["fingerprint_sha256"]:
            lines.append(f"SHA256: {result['public_key']['fingerprint_sha256']}")

        if result["public_key"]["fingerprint_md5"]:
            lines.append(f"MD5: {result['public_key']['fingerprint_md5']}")

        # Security warnings
        if result.get("security"):
            security = result["security"]
            if security.get("deprecated"):
                lines.append("⚠️  WARNING: Key uses deprecated algorithm")
            if security.get("insecure"):
                lines.append("❌ CRITICAL: Key is insecure")
            if security.get("warnings"):
                for warning in security["warnings"]:
                    lines.append(f"⚠️  {warning}")

        # Insights
        if result.get("insights"):
            insights = result["insights"]
            insight_parts = []
            if insights.get("local_user"):
                insight_parts.append(f"local_user={insights['local_user']}")
            if insights.get("host"):
                insight_parts.append(f"host={insights['host']}")
            if insights.get("ip_addresses"):
                insight_parts.append(f"ips={','.join(insights['ip_addresses'])}")

            if insight_parts:
                lines.append(f"Insights: {', '.join(insight_parts)}")

        # Validation results
        if validation_results:
            lines.append("")
            lines.append("Validation:")
            for server, result_data in validation_results.items():
                if result_data.get("reachable"):
                    if result_data.get(
                        "authenticated", True
                    ):  # Default to True for backward compatibility
                        if result_data.get("username"):
                            lines.append(f"- {server}: {result_data['username']} ✅")
                        elif result_data.get("requires_repo_path"):
                            lines.append(
                                f"- {server}: auth success, "
                                f"username=? (repo path required)"
                            )
                        else:
                            lines.append(f"- {server}: authenticated ✅")
                    else:
                        # Authentication failed
                        error = result_data.get("error", "authentication failed")
                        lines.append(f"- {server}: ❌ {error}")
                else:
                    error = result_data.get("error", "connection failed")
                    lines.append(f"- {server}: ❌ {error}")

                # Show verbose server response if requested
                if self.verbose and result_data.get("banner"):
                    banner = result_data["banner"]
                    if len(banner) > 100:
                        banner = banner[:97] + "..."
                    lines.append(f"    Server response: {banner}")

        # Repository discovery results
        if repo_discovery_results:
            lines.append("")
            lines.append("Repository Discovery Results:")

            username = repo_discovery_results.get("username")
            organizations = repo_discovery_results.get("organizations", [])
            repositories = repo_discovery_results.get("accessible_repositories", [])
            total = repo_discovery_results.get("total_attempts", 0)
            successful = repo_discovery_results.get("successful_attempts", 0)
            failed = repo_discovery_results.get("failed_attempts", 0)

            if username:
                lines.append(f"Identified user: {username}")

            if organizations:
                lines.append(f"Organizations: {', '.join(organizations)}")
                lines.append(
                    f"Targets for repository testing: "
                    f"{username} + {len(organizations)} org(s)"
                )
            else:
                lines.append("Organizations: none found")
                lines.append(f"Targets for repository testing: {username} only")

            # Show discovery method if available
            if repo_discovery_results.get("discovery_method"):
                method = repo_discovery_results["discovery_method"]
                api_available = repo_discovery_results.get("api_available", False)
                token_provided = repo_discovery_results.get("api_token_provided", False)

                if method == "api":
                    lines.append("Discovery method: GitHub API ✅")
                elif method == "heuristic" and api_available:
                    if not token_provided:
                        lines.append(
                            "Discovery method: heuristic "
                            "(💡 tip: provide GitHub token for better results)"
                        )
                    else:
                        lines.append("Discovery method: heuristic (API fallback)")
                else:
                    lines.append("Discovery method: heuristic")

            lines.append(f"Total attempts: {total}")
            lines.append(f"Accessible repositories: {successful}")
            lines.append(f"Failed attempts: {failed}")

            if repositories:
                lines.append("Found repositories:")
                for repo in repositories:
                    repo_type = "👤" if repo["type"] == "user" else "🏢"
                    lines.append(f"  {repo_type} {repo['full_name']} ({repo['type']})")

            if repo_discovery_results.get("errors"):
                lines.append("Errors:")
                for error in repo_discovery_results["errors"][
                    :5
                ]:  # Limit error display
                    lines.append(f"  - {error}")
                if len(repo_discovery_results["errors"]) > 5:
                    lines.append(
                        f"  ... and "
                        f"{len(repo_discovery_results['errors']) - 5} more errors"
                    )

        return "\n".join(lines)

    def _format_organization_discovery_human_readable(
        self, org_discovery_results: Dict[str, Any]
    ) -> str:
        """Format organization discovery results in human-readable format."""
        lines = []

        lines.append("")
        lines.append("Organization Discovery:")

        username = org_discovery_results.get("username")
        organizations = org_discovery_results.get("organizations", [])
        discovery_method = org_discovery_results.get("discovery_method")
        error = org_discovery_results.get("error")

        if error:
            lines.append(f"❌ Error: {error}")
            return "\n".join(lines)

        if username:
            lines.append(f"Identified user: {username}")

        if organizations:
            lines.append(f"Found organizations: {', '.join(organizations)}")
            lines.append(f"Total organizations: {len(organizations)}")
        else:
            lines.append("Found organizations: none")

        # Show discovery method and API info
        if discovery_method == "api":
            lines.append("Discovery method: GitHub API ✅")
        elif discovery_method == "heuristic":
            api_available = org_discovery_results.get("api_available", False)
            api_token_provided = org_discovery_results.get("api_token_provided", False)

            if api_available and not api_token_provided:
                lines.append(
                    "Discovery method: heuristic "
                    "(💡 tip: provide GitHub token for better results)"
                )
            elif api_available:
                lines.append("Discovery method: heuristic (API fallback)")
            else:
                lines.append("Discovery method: heuristic")

        return "\n".join(lines)

    def _format_single_validation_result_human_readable(
        self, server_name: str, result: Dict[str, Any]
    ) -> str:
        """Format a single validation result in human-readable format."""
        lines = []

        if result.get("reachable"):
            if result.get(
                "authenticated", True
            ):  # Default to True for backward compatibility
                if result.get("username"):
                    lines.append(f"- {server_name}: {result['username']} ✅")
                elif result.get("requires_repo_path"):
                    lines.append(
                        f"- {server_name}: auth success, "
                        f"username=? (repo path required)"
                    )
                else:
                    lines.append(f"- {server_name}: authenticated ✅")
            else:
                # Authentication failed
                error = result.get("error", "authentication failed")
                lines.append(f"- {server_name}: ❌ Authentication failed")
                if self.verbose and error:
                    lines.append(f"    Server response: {error}")
        else:
            # Connection failed
            error = result.get("error", "connection failed")
            lines.append(f"- {server_name}: ❌ Connection failed")
            if self.verbose and error:
                lines.append(f"    Error: {error}")

        # Add verbose server response if available
        if self.verbose and result.get("banner"):
            banner = result["banner"]
            if len(banner) > 100:
                banner = banner[:97] + "..."
            lines.append(f"    Server response: {banner}")

        return "\n".join(lines)

    def _format_key_analysis_human_readable(self, result: Dict[str, Any]) -> str:
        """Format key analysis results in human-readable format."""
        lines = []

        # Key information
        lines.append(f"Key: {result['input']}")
        lines.append(f"Type: {result['key']['type']}")

        if result["key"]["bits"]:
            lines.append(f"Bits: {result['key']['bits']}")

        if result["key"].get("curve"):
            lines.append(f"Curve: {result['key']['curve']}")

        passphrase_status = "YES" if result["key"]["passphrase"] else "NO"
        lines.append(f"Passphrase: {passphrase_status}")

        # Public key info
        if result["public_key"]["key_string"]:
            pub_key = result["public_key"]["key_string"]
            if len(pub_key) > 80:
                pub_key = pub_key[:77] + "..."
            lines.append(f"Public: {pub_key}")

        if result["public_key"]["comment"]:
            lines.append(f"Comment: {result['public_key']['comment']}")

        # Fingerprints
        if result["public_key"]["fingerprint_sha256"]:
            lines.append(f"SHA256: {result['public_key']['fingerprint_sha256']}")

        if result["public_key"]["fingerprint_md5"]:
            lines.append(f"MD5: {result['public_key']['fingerprint_md5']}")

        # Security warnings
        if result.get("security"):
            security = result["security"]
            if security.get("deprecated"):
                lines.append("⚠️  WARNING: Key uses deprecated algorithm")
            if security.get("insecure"):
                lines.append("❌ CRITICAL: Key is insecure")
            if security.get("warnings"):
                for warning in security["warnings"]:
                    lines.append(f"⚠️  {warning}")

        # Insights
        if result.get("insights"):
            insights = result["insights"]
            insight_parts = []
            if insights.get("local_user"):
                insight_parts.append(f"local_user={insights['local_user']}")
            if insights.get("host"):
                insight_parts.append(f"host={insights['host']}")
            if insights.get("ip_addresses"):
                insight_parts.append(f"ips={','.join(insights['ip_addresses'])}")

            if insight_parts:
                lines.append(f"Insights: {', '.join(insight_parts)}")

        return "\n".join(lines)

    def _format_validation_results_human_readable(
        self, validation_results: Dict[str, Any]
    ) -> str:
        """Format validation results in human-readable format."""
        lines = []

        for server, result_data in validation_results.items():
            if result_data.get("reachable"):
                if result_data.get(
                    "authenticated", True
                ):  # Default to True for backward compatibility
                    if result_data.get("username"):
                        lines.append(f"- {server}: {result_data['username']} ✅")
                    elif result_data.get("requires_repo_path"):
                        lines.append(
                            f"- {server}: auth success, username=? (repo path required)"
                        )
                    else:
                        lines.append(f"- {server}: authenticated ✅")
                else:
                    # Authentication failed
                    error = result_data.get("error", "authentication failed")
                    lines.append(f"- {server}: ❌ {error}")
            else:
                error = result_data.get("error", "connection failed")
                lines.append(f"- {server}: ❌ {error}")

            # Show verbose server response if requested
            if self.verbose and result_data.get("banner"):
                banner = result_data["banner"]
                if len(banner) > 100:
                    banner = banner[:97] + "..."
                lines.append(f"    Server response: {banner}")

        return "\n".join(lines)

    def _format_repository_discovery_human_readable(
        self, repo_discovery_results: Dict[str, Any]
    ) -> str:
        """Format repository discovery results in human-readable format."""
        lines = []

        lines.append("")
        lines.append("Repository Discovery Results:")

        repositories = repo_discovery_results.get("accessible_repositories", [])
        total = repo_discovery_results.get("total_attempts", 0)
        successful = repo_discovery_results.get("successful_attempts", 0)
        failed = repo_discovery_results.get("failed_attempts", 0)

        lines.append(f"Total attempts: {total}")
        lines.append(f"Accessible repositories: {successful}")
        lines.append(f"Failed attempts: {failed}")

        if repositories:
            # Group repositories by owner (user/organization)
            repos_by_owner: Dict[str, List[Dict[str, Any]]] = {}
            for repo in repositories:
                owner = repo["owner"]
                if owner not in repos_by_owner:
                    repos_by_owner[owner] = []
                repos_by_owner[owner].append(repo)

            # Display results per owner
            for owner, owner_repos in repos_by_owner.items():
                owner_type = (
                    "👤 User" if owner_repos[0]["type"] == "user" else "🏢 Organization"
                )
                lines.append(f"\n{owner_type}: {owner}")
                for repo in owner_repos:
                    lines.append(f"  📁 {repo['repository']}")
                    if repo.get("web_url"):
                        lines.append(f"    🔗 {repo['web_url']}")
        else:
            lines.append("\nNo accessible repositories found.")

        if repo_discovery_results.get("errors"):
            lines.append("\nErrors:")
            for error in repo_discovery_results["errors"][:5]:  # Limit error display
                lines.append(f"  - {error}")
            if len(repo_discovery_results["errors"]) > 5:
                lines.append(
                    f"  ... and {len(repo_discovery_results['errors']) - 5} more errors"
                )

        return "\n".join(lines)

    def print_error(self, message: str, exit_code: Optional[int] = None) -> None:
        """Print error message and optionally exit."""
        print(f"❌ Error: {message}", file=sys.stderr)

        if exit_code is not None:
            sys.exit(exit_code)

    def print_verbose(self, message: str) -> None:
        """Print verbose/debug message."""
        print(f"🔍 {message}", file=sys.stderr)
