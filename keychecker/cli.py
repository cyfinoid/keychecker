"""
Command-line interface for KeyChecker.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional

from keychecker.core.key_analyzer import SSHKeyAnalyzer
from keychecker.core.server_validator import ServerValidator
from keychecker.utils.output import OutputFormatter


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog='keychecker',
        description='SSH private key fingerprinting and Git hosting account discovery tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  keychecker -i ~/.ssh/id_ed25519                    # Analyze key + validate all servers
  keychecker -i ~/.ssh/id_ed25519 --no-validate     # Analyze key only (no server validation)
  keychecker -i ~/.ssh/id_rsa --validate github     # Validate against GitHub only
  keychecker -i ~/.ssh/id_rsa --validate            # Validate against no servers
  keychecker -i ~/.ssh/id_rsa --bruteforce --server gitlab --wordlist usernames.txt
  keychecker -i ~/.ssh/id_rsa --json --public-out public_key.pub

Exit codes:
  0 - success
  1 - runtime/IO/argument error  
  2 - all servers unreachable
  3 - bruteforce attempted, no match found
  4 - key parsed but flagged (deprecated/insecure)
        """
    )
    
    # Required arguments
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Path to private key file (required)'
    )
    
    # Validation options
    parser.add_argument(
        '--validate',
        nargs='*',
        choices=['github', 'gitlab', 'bitbucket'],
        help='One or more servers to validate against (default: all supported servers)'
    )
    
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip server validation (only analyze key locally)'
    )
    
    # Bruteforce options
    parser.add_argument(
        '--bruteforce',
        action='store_true',
        help='Enable username enumeration strategy'
    )
    
    parser.add_argument(
        '--server',
        choices=['github', 'gitlab', 'bitbucket'],
        help='Server shortname (used with --bruteforce)'
    )
    
    parser.add_argument(
        '--wordlist',
        help='File with candidate usernames'
    )
    
    # Output options
    parser.add_argument(
        '--json',
        action='store_true',
        help='JSON output mode'
    )
    
    parser.add_argument(
        '--public-out',
        help='Save derived public key to file'
    )
    
    parser.add_argument(
        '--no-banner',
        action='store_true',
        help='Suppress banner output'
    )
    
    # Connection options
    parser.add_argument(
        '--timeout',
        type=int,
        default=5,
        help='Per-connection timeout (default: 5s)'
    )
    
    parser.add_argument(
        '--concurrency',
        type=int,
        default=10,
        help='Parallel connections (default: 10)'
    )
    
    parser.add_argument(
        '--known-hosts',
        help='Path to known_hosts file'
    )
    
    # Debug options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Debug/trace logs'
    )
    
    return parser


async def run_analysis(args) -> int:
    """Run the key analysis with the given arguments."""
    # Initialize components
    analyzer = SSHKeyAnalyzer()
    validator = ServerValidator(timeout=args.timeout, concurrency=args.concurrency)
    formatter = OutputFormatter(json_mode=args.json, no_banner=args.no_banner, verbose=args.verbose)
    
    # Print banner
    formatter.print_banner()
    
    try:
        # Analyze the key
        if args.verbose:
            formatter.print_verbose(f"Analyzing key: {args.input}")
            
        analysis_result = analyzer.analyze_key_file(args.input)
        
        # Save public key if requested
        if args.public_out and analysis_result['public_key']['key_string']:
            with open(args.public_out, 'w') as f:
                f.write(analysis_result['public_key']['key_string'] + '\n')
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
                servers_to_validate = ['github', 'gitlab', 'bitbucket']
        
        # Validate against servers
        validation_results = None
        if servers_to_validate:
            if args.verbose:
                formatter.print_verbose(f"Validating against servers: {', '.join(servers_to_validate)}")
            validation_results = await validator.validate_servers(args.input, servers_to_validate)
        
        # Run bruteforce if requested
        bruteforce_results = None
        if args.bruteforce:
            if not args.server:
                formatter.print_error("--server is required when using --bruteforce", 1)
            if not args.wordlist:
                formatter.print_error("--wordlist is required when using --bruteforce", 1)
                
            if args.verbose:
                formatter.print_verbose(f"Running bruteforce against {args.server}")
            bruteforce_results = await validator.bruteforce_username(
                args.input, args.server, args.wordlist
            )
        
        # Format and print results
        output = formatter.format_analysis_result(
            analysis_result, validation_results, bruteforce_results
        )
        print(output)
        
        # Determine exit code
        exit_code = 0
        
        # Check for security issues
        if analysis_result.get('security'):
            security = analysis_result['security']
            if security.get('deprecated') or security.get('insecure'):
                exit_code = 4
        
        # Check validation results
        if validation_results:
            all_unreachable = all(
                not result.get('reachable', False) 
                for result in validation_results.values()
            )
            if all_unreachable:
                exit_code = 2
        
        # Check bruteforce results
        if bruteforce_results:
            successful_usernames = bruteforce_results.get('successful_usernames', [])
            if not successful_usernames:
                exit_code = 3
        
        return exit_code
        
    except FileNotFoundError as e:
        formatter.print_error(f"File not found: {e}", 1)
    except ValueError as e:
        formatter.print_error(f"Invalid key or argument: {e}", 1)
    except Exception as e:
        if args.verbose:
            import traceback
            formatter.print_verbose(f"Full traceback:\n{traceback.format_exc()}")
        formatter.print_error(f"Unexpected error: {e}", 1)


def validate_args(args) -> None:
    """Validate command line arguments."""
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"❌ Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    # Validate bruteforce arguments
    if args.bruteforce:
        if not args.server:
            print("❌ Error: --server is required when using --bruteforce", file=sys.stderr)
            sys.exit(1)
        if not args.wordlist:
            print("❌ Error: --wordlist is required when using --bruteforce", file=sys.stderr)
            sys.exit(1)
        if not os.path.exists(args.wordlist):
            print(f"❌ Error: Wordlist file not found: {args.wordlist}", file=sys.stderr)
            sys.exit(1)
    
    # Validate argument combinations
    if args.validate is not None and args.no_validate:
        print("❌ Error: Cannot use both --validate and --no-validate", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
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


if __name__ == '__main__':
    sys.exit(main())
