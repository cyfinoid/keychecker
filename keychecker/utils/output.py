"""
Output formatting utilities for human-readable and JSON modes.
"""

import json
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime


class OutputFormatter:
    """Handles output formatting in different modes."""
    
    def __init__(self, json_mode: bool = False, no_banner: bool = False, verbose: bool = False):
        self.json_mode = json_mode
        self.no_banner = no_banner
        self.verbose = verbose
    
    def print_banner(self):
        """Print application banner."""
        if self.no_banner or self.json_mode:
            return
            
        banner = """
🔑 KeyChecker - SSH Key Analysis Tool
=====================================
"""
        print(banner)
    
    def format_analysis_result(self, result: Dict[str, Any], 
                             validation_results: Optional[Dict[str, Any]] = None,
                             bruteforce_results: Optional[Dict[str, Any]] = None) -> str:
        """Format the complete analysis result."""
        if self.json_mode:
            return self._format_json(result, validation_results, bruteforce_results)
        else:
            return self._format_human_readable(result, validation_results, bruteforce_results)
    
    def _format_json(self, result: Dict[str, Any],
                    validation_results: Optional[Dict[str, Any]] = None,
                    bruteforce_results: Optional[Dict[str, Any]] = None) -> str:
        """Format output as JSON."""
        output = {
            "timestamp": datetime.now().isoformat(),
            "analysis": result
        }
        
        if validation_results:
            output["validation"] = validation_results
            
        if bruteforce_results:
            output["bruteforce"] = bruteforce_results
            
        return json.dumps(output, indent=2)
    
    def _format_human_readable(self, result: Dict[str, Any],
                             validation_results: Optional[Dict[str, Any]] = None,
                             bruteforce_results: Optional[Dict[str, Any]] = None) -> str:
        """Format output in human-readable format."""
        lines = []
        
        # Key information
        lines.append(f"Key: {result['input']}")
        lines.append(f"Type: {result['key']['type']}")
        
        if result['key']['bits']:
            lines.append(f"Bits: {result['key']['bits']}")
            
        if result['key'].get('curve'):
            lines.append(f"Curve: {result['key']['curve']}")
            
        passphrase_status = "YES" if result['key']['passphrase'] else "NO"
        lines.append(f"Passphrase: {passphrase_status}")
        
        # Public key info
        if result['public_key']['key_string']:
            pub_key = result['public_key']['key_string']
            if len(pub_key) > 80:
                pub_key = pub_key[:77] + "..."
            lines.append(f"Public: {pub_key}")
            
        if result['public_key']['comment']:
            lines.append(f"Comment: {result['public_key']['comment']}")
            
        # Fingerprints
        if result['public_key']['fingerprint_sha256']:
            lines.append(f"SHA256: {result['public_key']['fingerprint_sha256']}")
            
        if result['public_key']['fingerprint_md5']:
            lines.append(f"MD5: {result['public_key']['fingerprint_md5']}")
        
        # Security warnings
        if result.get('security'):
            security = result['security']
            if security.get('deprecated'):
                lines.append("⚠️  WARNING: Key uses deprecated algorithm")
            if security.get('insecure'):
                lines.append("❌ CRITICAL: Key is insecure")
            if security.get('warnings'):
                for warning in security['warnings']:
                    lines.append(f"⚠️  {warning}")
        
        # Insights
        if result.get('insights'):
            insights = result['insights']
            insight_parts = []
            if insights.get('local_user'):
                insight_parts.append(f"local_user={insights['local_user']}")
            if insights.get('host'):
                insight_parts.append(f"host={insights['host']}")
            if insights.get('ip_addresses'):
                insight_parts.append(f"ips={','.join(insights['ip_addresses'])}")
            
            if insight_parts:
                lines.append(f"Insights: {', '.join(insight_parts)}")
        
        # Validation results
        if validation_results:
            lines.append("")
            lines.append("Validation:")
            for server, result_data in validation_results.items():
                if result_data.get('reachable'):
                    if result_data.get('authenticated', True):  # Default to True for backward compatibility
                        if result_data.get('username'):
                            lines.append(f"- {server}: {result_data['username']} ✅")
                        elif result_data.get('requires_repo_path'):
                            lines.append(f"- {server}: auth success, username=? (repo path required)")
                        else:
                            lines.append(f"- {server}: authenticated ✅")
                    else:
                        # Authentication failed
                        error = result_data.get('error', 'authentication failed')
                        lines.append(f"- {server}: ❌ {error}")
                else:
                    error = result_data.get('error', 'connection failed')
                    lines.append(f"- {server}: ❌ {error}")
                
                # Show verbose server response if requested
                if self.verbose and result_data.get('banner') and not self.json_mode:
                    banner = result_data['banner']
                    if len(banner) > 100:
                        banner = banner[:97] + "..."
                    lines.append(f"    Server response: {banner}")
        
        # Bruteforce results
        if bruteforce_results:
            lines.append("")
            lines.append("Bruteforce Results:")
            total = bruteforce_results.get('total_attempts', 0)
            successful = bruteforce_results.get('successful_usernames', [])
            failed = bruteforce_results.get('failed_attempts', 0)
            
            lines.append(f"Total attempts: {total}")
            lines.append(f"Successful: {len(successful)}")
            lines.append(f"Failed: {failed}")
            
            if successful:
                lines.append("Found usernames:")
                for user_data in successful:
                    lines.append(f"  - {user_data['username']} ({user_data['repository']})")
            
            if bruteforce_results.get('errors'):
                lines.append("Errors:")
                for error in bruteforce_results['errors'][:5]:  # Limit error display
                    lines.append(f"  - {error}")
                if len(bruteforce_results['errors']) > 5:
                    lines.append(f"  ... and {len(bruteforce_results['errors']) - 5} more errors")
        
        return "\n".join(lines)
    
    def print_error(self, message: str, exit_code: Optional[int] = None):
        """Print error message and optionally exit."""
        if self.json_mode:
            error_output = {
                "error": message,
                "timestamp": datetime.now().isoformat()
            }
            print(json.dumps(error_output, indent=2), file=sys.stderr)
        else:
            print(f"❌ Error: {message}", file=sys.stderr)
        
        if exit_code is not None:
            sys.exit(exit_code)
    
    def print_verbose(self, message: str):
        """Print verbose/debug message."""
        if not self.json_mode:
            print(f"🔍 {message}", file=sys.stderr)
