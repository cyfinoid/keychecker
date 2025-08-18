"""
Command-line interface for KeyChecker.
"""

import argparse
import asyncio
import os
import sys
from typing import Any

from keychecker.core.key_analyzer import SSHKeyAnalyzer
from keychecker.core.server_validator import ServerValidator
from keychecker.utils.output import OutputFormatter


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="keychecker",
        description=(
            "SSH private key fingerprinting and Git hosting repository discovery tool"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  keychecker ~/.ssh/id_ed25519                      # Analyze key + validate all servers
  keychecker -i ~/.ssh/id_ed25519                   # Analyze key + validate all servers
  keychecker ~/.ssh/id_ed25519 --no-validate       # Analyze key only
  keychecker ~/.ssh/id_rsa --validate github       # Validate against GitHub only
  keychecker ~/.ssh/id_rsa --validate github --discovery repo_names.txt
  keychecker ~/.ssh/id_rsa --public-out public_key.pub

Exit codes:
  0 - success
  1 - runtime/IO/argument error
  2 - all servers unreachable
  3 - repository discovery attempted, no repositories found
  4 - key parsed but flagged (deprecated/insecure)
        """,
    )

    # Positional argument for key file (optional if -i is used)
    parser.add_argument("key_file", nargs="?", help="Path to private key file")

    # Optional explicit input flag
    parser.add_argument(
        "-i",
        "--input",
        help="Path to private key file (alternative to positional argument)",
    )

    # Validation and discovery options
    parser.add_argument(
        "--validate",
        nargs="*",
        choices=["github", "gitlab", "bitbucket", "codeberg", "gitea", "huggingface"],
        help=(
            "One or more servers to validate against (default: all supported servers). "
            "When used with --discover-repos, specifies which server to use for "
            "repository discovery."
        ),
    )

    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip server validation (only analyze key locally)",
    )

    # Repository discovery options
    parser.add_argument(
        "--discovery",
        help=(
            "File with candidate repository names (not usernames). When specified, "
            "enables repository discovery mode."
        ),
    )

    # API options
    parser.add_argument(
        "--github-token",
        help=(
            "GitHub API token for enhanced organization discovery "
            "(or set GITHUB_TOKEN env var)"
        ),
    )

    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars during repository discovery",
    )

    # Output options
    parser.add_argument("--public-out", help="Save derived public key to file")

    parser.add_argument(
        "--no-banner", action="store_true", help="Suppress banner output"
    )

    # Connection options
    parser.add_argument(
        "--timeout", type=int, default=5, help="Per-connection timeout (default: 5s)"
    )

    parser.add_argument(
        "--concurrency", type=int, default=10, help="Parallel connections (default: 10)"
    )

    # Debug options
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug/trace logs")

    return parser


async def run_analysis(args: Any) -> int:
    """Run the key analysis with the given arguments."""
    # Get GitHub token from CLI arg or environment
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")

    # Initialize components
    analyzer = SSHKeyAnalyzer()
    validator = ServerValidator(
        timeout=args.timeout,
        concurrency=args.concurrency,
        github_token=github_token,
        show_progress=not args.no_progress,
    )
    formatter = OutputFormatter(no_banner=args.no_banner, verbose=args.verbose)

    # Print banner
    formatter.print_banner()

    try:
        # Analyze the key
        if args.verbose:
            formatter.print_verbose(f"Analyzing key: {args.input_file}")

        analysis_result = analyzer.analyze_key_file(args.input_file)

        # Print key analysis results immediately
        key_output = formatter.format_key_analysis(analysis_result)
        print(key_output)
        sys.stdout.flush()  # Ensure output is displayed immediately

        # Save public key if requested
        if args.public_out and analysis_result["public_key"]["key_string"]:
            with open(args.public_out, "w") as f:
                f.write(analysis_result["public_key"]["key_string"] + "\n")
            if args.verbose:
                formatter.print_verbose(f"Public key saved to: {args.public_out}")

        # Determine which servers to validate against
        servers_to_validate = None
        if not args.no_validate:
            if args.validate is not None:
                # User specified servers explicitly (could be empty list for none)
                servers_to_validate = args.validate
            else:
                # Default: validate against all supported servers
                servers_to_validate = [
                    "github",
                    "gitlab",
                    "bitbucket",
                    "codeberg",
                    "gitea",
                    "huggingface",
                ]

        # Validate against servers
        validation_results = None
        if servers_to_validate:
            if args.verbose:
                formatter.print_verbose(
                    f"Validating against servers: {', '.join(servers_to_validate)}"
                )

            # Print validation header
            print("")
            print("Validation:")
            sys.stdout.flush()  # Ensure header is displayed immediately

            # Temporarily disable progress to prevent interference with validation
            for provider in validator.providers.values():
                provider._progress_enabled = False

            # Use streaming validation to show results as they complete
            validation_results = {}
            async for server_name, result in validator.validate_servers_streaming(
                args.input_file, servers_to_validate
            ):
                validation_results[server_name] = result

                # Print individual validation result immediately
                validation_output = formatter.format_single_validation_result(
                    server_name, result
                )
                print(validation_output)
                sys.stdout.flush()  # Ensure output is displayed immediately

            # Restore progress setting
            for provider in validator.providers.values():
                provider._progress_enabled = provider.show_progress

        # Add a clear line after validation to prevent progress bar interference
        print("")
        sys.stdout.flush()

        # Run repository discovery if requested
        repo_discovery_results = None
        if args.discovery:
            # For repository discovery, we need exactly one server specified
            if not args.validate or len(args.validate) != 1:
                formatter.print_error(
                    "Repository discovery requires exactly one server specified "
                    "with --validate",
                    1,
                )

            target_server = args.validate[0]
            if args.verbose:
                formatter.print_verbose(
                    f"Running repository discovery against {target_server}"
                )

            # First, discover organizations and show them immediately
            org_discovery_info = await validator.discover_organizations_only(
                args.input_file, target_server
            )
            if org_discovery_info:
                org_output = formatter.format_organization_discovery(org_discovery_info)
                print(org_output)
                sys.stdout.flush()  # Ensure output is displayed immediately

            # Then run full repository discovery
            repo_discovery_results = await validator.discover_repositories(
                args.input_file, target_server, args.discovery
            )

            # Add a clear line after progress bars before showing results
            print("")
            sys.stdout.flush()

            # Print repository discovery results immediately
            repo_output = formatter.format_repository_discovery_results(
                repo_discovery_results
            )
            print(repo_output)
            sys.stdout.flush()  # Ensure output is displayed immediately

        # Determine exit code
        exit_code = 0

        # Check for security issues
        if analysis_result.get("security"):
            security = analysis_result["security"]
            if security.get("deprecated") or security.get("insecure"):
                exit_code = 4

        # Check validation results
        if validation_results:
            all_unreachable = all(
                not result.get("reachable", False)
                for result in validation_results.values()
            )
            if all_unreachable:
                exit_code = 2

        # Check repository discovery results
        if repo_discovery_results:
            accessible_repos = repo_discovery_results.get("accessible_repositories", [])
            if not accessible_repos:
                exit_code = 3

        return exit_code

    except FileNotFoundError as e:
        formatter.print_error(f"File not found: {e}", 1)
        return 1
    except ValueError as e:
        formatter.print_error(f"Invalid key or argument: {e}", 1)
        return 1
    except Exception as e:
        if args.verbose:
            import traceback

            formatter.print_verbose(f"Full traceback:\n{traceback.format_exc()}")
        formatter.print_error(f"Unexpected error: {e}", 1)
        return 1
    finally:
        # Clean up resources
        if validator:
            try:
                await validator.cleanup()
            except Exception:
                # Ignore cleanup errors
                pass


def validate_args(args: Any) -> None:
    """Validate command line arguments."""
    # Determine the input file path
    if args.input and args.key_file:
        print(
            "❌ Error: Cannot specify both positional argument and -i/--input flag",
            file=sys.stderr,
        )
        sys.exit(1)
    elif args.input:
        args.input_file = args.input
    elif args.key_file:
        args.input_file = args.key_file
    else:
        print(
            "❌ Error: Must specify a private key file either as positional argument "
            "or with -i/--input",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"❌ Error: Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    # Validate repository discovery arguments
    if args.discovery:
        if not args.validate or len(args.validate) != 1:
            print(
                "❌ Error: Repository discovery requires exactly one server specified "
                "with --validate",
                file=sys.stderr,
            )
            sys.exit(1)
        if not os.path.exists(args.discovery):
            print(
                f"❌ Error: Discovery file not found: {args.discovery}", file=sys.stderr
            )
            sys.exit(1)

    # Validate argument combinations
    if args.validate is not None and args.no_validate:
        print("❌ Error: Cannot use both --validate and --no-validate", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # If no key file is specified, show help
    if not args.key_file and not args.input:
        parser.print_help()
        return 0

    # Validate arguments
    validate_args(args)

    # Run the analysis
    try:
        return asyncio.run(run_analysis(args))
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
