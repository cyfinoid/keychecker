"""
Git server validation functionality for GitHub, GitLab, Bitbucket, etc.
"""

import asyncio
import asyncssh
import socket
import re
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ServerConfig:
    """Configuration for a Git server."""
    name: str
    hostname: str
    port: int = 22
    username: str = "git"


class ServerValidator:
    """Validates SSH keys against Git hosting servers."""
    
    SERVERS = {
        'github': ServerConfig('github', 'github.com'),
        'gitlab': ServerConfig('gitlab', 'gitlab.com'), 
        'bitbucket': ServerConfig('bitbucket', 'bitbucket.org'),
    }
    
    def __init__(self, timeout: int = 5, concurrency: int = 10):
        self.timeout = timeout
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
    
    async def validate_servers(self, private_key_path: str, server_names: List[str]) -> Dict[str, Any]:
        """
        Validate SSH key against multiple servers.
        
        Args:
            private_key_path: Path to SSH private key
            server_names: List of server names to validate against
            
        Returns:
            Dictionary with validation results for each server
        """
        results = {}
        
        # Create validation tasks
        tasks = []
        for server_name in server_names:
            if server_name.lower() in self.SERVERS:
                server = self.SERVERS[server_name.lower()]
                task = self._validate_server(private_key_path, server)
                tasks.append((server_name, task))
        
        # Execute validations concurrently
        for server_name, task in tasks:
            try:
                result = await task
                results[server_name] = result
            except Exception as e:
                results[server_name] = {
                    'reachable': False,
                    'error': str(e),
                    'username': None
                }
        
        return results
    
    async def _validate_server(self, private_key_path: str, server: ServerConfig) -> Dict[str, Any]:
        """Validate SSH key against a single server."""
        async with self.semaphore:
            # Use actual SSH command for more accurate results
            return await self._validate_with_ssh_command(private_key_path, server)
    
    async def _validate_with_ssh_command(self, private_key_path: str, server: ServerConfig) -> Dict[str, Any]:
        """Validate using actual SSH command for more accurate results."""
        try:
            # Build SSH command
            cmd = [
                'ssh',
                '-i', private_key_path,
                '-o', 'StrictHostKeyChecking=no',  # Skip host key verification
                '-o', 'UserKnownHostsFile=/dev/null',  # Don't save host keys
                '-o', f'ConnectTimeout={self.timeout}',
                '-o', 'BatchMode=yes',  # Non-interactive
                '-o', 'LogLevel=ERROR',  # Reduce noise
                f'{server.username}@{server.hostname}'
            ]
            
            if server.port != 22:
                cmd.extend(['-p', str(server.port)])
            
            # Run SSH command
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout * 2
            )
            
            # Combine stdout and stderr for analysis
            output = (stdout.decode('utf-8', errors='ignore') + stderr.decode('utf-8', errors='ignore')).strip()
            
            # Parse the output
            return self._parse_ssh_output(output, proc.returncode, server)
            
        except asyncio.TimeoutError:
            return {
                'reachable': False,
                'error': f'Connection timeout after {self.timeout}s',
                'username': None,
                'authenticated': False
            }
        except Exception as e:
            return {
                'reachable': False,
                'error': f'SSH command failed: {str(e)}',
                'username': None,
                'authenticated': False
            }
    
    def _parse_ssh_output(self, output: str, exit_code: int, server: ServerConfig) -> Dict[str, Any]:
        """Parse SSH command output to determine authentication status."""
        output_lower = output.lower()
        
        # GitHub success pattern
        if server.name == 'github':
            if 'hi ' in output_lower and 'successfully authenticated' in output_lower:
                # Extract username from "Hi username!"
                match = re.search(r'Hi (\w+)!', output, re.IGNORECASE)
                username = match.group(1) if match else None
                return {
                    'reachable': True,
                    'authenticated': True,
                    'username': username,
                    'banner': output
                }
        
        # Success patterns for other servers
        success_patterns = [
            'successfully authenticated',
            'welcome to gitlab',
            'shell access',
            'does not provide shell access'
        ]
        
        if any(pattern in output_lower for pattern in success_patterns):
            # Try to extract username from various patterns
            username = None
            username_patterns = [
                r'Hi (\w+)!',
                r'Hello (\w+)',
                r'Welcome to GitLab, @?(\w+)!?'
            ]
            for pattern in username_patterns:
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    username = match.group(1)
                    break
                    
            return {
                'reachable': True,
                'authenticated': True,
                'username': username,
                'banner': output
            }
        
        # Authentication failure patterns
        auth_failure_patterns = [
            'permission denied (publickey)',
            'permission denied for user',
            'authentication failed',
            'no supported authentication methods',
            'publickey authentication failed'
        ]
        
        if any(pattern in output_lower for pattern in auth_failure_patterns):
            return {
                'reachable': True,
                'authenticated': False,
                'username': None,
                'error': 'Authentication failed - key not authorized',
                'banner': output
            }
        
        # Host key verification failed or other connection issues
        connection_failure_patterns = [
            'host key verification failed',
            'connection refused',
            'connection timed out',
            'network is unreachable'
        ]
        
        if any(pattern in output_lower for pattern in connection_failure_patterns):
            return {
                'reachable': False,
                'error': 'Connection failed - ' + output.split('\n')[0][:50],
                'username': None,
                'authenticated': False
            }
        
        # Default case - if we can't determine, assume auth failure if exit code != 0
        if exit_code != 0:
            return {
                'reachable': True,
                'authenticated': False,
                'username': None,
                'error': 'Authentication failed - unknown error',
                'banner': output
            }
        
        # Successful connection (shouldn't happen with Git servers)
        return {
            'reachable': True,
            'authenticated': True,
            'username': None,
            'banner': output
        }
    
    async def _parse_git_response(self, exception, server: ServerConfig) -> Dict[str, Any]:
        """Parse Git server response to extract username information."""
        error_msg = str(exception)
        
        result = {
            'reachable': True,
            'authenticated': True,
            'username': None,
            'banner': error_msg,
            'requires_repo_path': False
        }
        
        # GitHub typically returns: "Hi username! You've successfully authenticated..."
        if server.name == 'github':
            # GitHub success patterns
            github_patterns = [
                r'Hi (\w+)!\s+You\'?ve successfully authenticated',
                r'Hi (\w+)!',
                r'Hello (\w+)',
                r'successfully authenticated.*?(\w+)',
            ]
            
            username_found = False
            for pattern in github_patterns:
                match = re.search(pattern, error_msg, re.IGNORECASE)
                if match:
                    result['username'] = match.group(1)
                    username_found = True
                    break
            
            # If no username found but contains success indicators, still mark as authenticated
            if not username_found and any(phrase in error_msg.lower() for phrase in [
                'successfully authenticated',
                'shell access',
                'does not provide shell access'
            ]):
                result['authenticated'] = True
        
        # GitLab and Bitbucket often require repository path
        elif server.name in ['gitlab', 'bitbucket']:
            if any(phrase in error_msg.lower() for phrase in [
                'repository not found',
                'repository does not exist', 
                'fatal: repository',
                'does not appear to be a git repository'
            ]):
                result['requires_repo_path'] = True
                result['username'] = None  # Can't determine without repo path
            else:
                # Try to extract username from various patterns
                patterns = [
                    r'Welcome to GitLab, @(\w+)!',
                    r'Welcome to GitLab, (\w+)!',
                    r'Hello (\w+)',
                    r'Hi (\w+)',
                    r'authenticated.*?(\w+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, error_msg, re.IGNORECASE)
                    if match:
                        result['username'] = match.group(1)
                        break
        
        return result
    
    async def bruteforce_username(self, private_key_path: str, server_name: str, 
                                wordlist_path: str) -> Dict[str, Any]:
        """
        Bruteforce username using git ls-remote with candidate usernames.
        
        Args:
            private_key_path: Path to SSH private key
            server_name: Server to bruteforce against
            wordlist_path: Path to wordlist file with candidate usernames
            
        Returns:
            Dictionary with bruteforce results
        """
        if server_name.lower() not in self.SERVERS:
            raise ValueError(f"Unsupported server: {server_name}")
        
        server = self.SERVERS[server_name.lower()]
        
        # Load wordlist
        try:
            with open(wordlist_path, 'r') as f:
                usernames = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            raise FileNotFoundError(f"Wordlist not found: {wordlist_path}")
        
        results = {
            'server': server_name,
            'total_attempts': len(usernames),
            'successful_usernames': [],
            'failed_attempts': 0,
            'errors': []
        }
        
        # Create semaphore for controlling concurrency
        sem = asyncio.Semaphore(self.concurrency)
        
        async def test_username(username: str):
            """Test a single username."""
            async with sem:
                try:
                    # Construct repository URL
                    repo_url = f"git@{server.hostname}:{username}/{username}.git"
                    
                    # Use asyncssh to test git ls-remote
                    proc = await asyncio.create_subprocess_exec(
                        'git', 'ls-remote', repo_url,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        env={'GIT_SSH_COMMAND': f'ssh -i {private_key_path} -o StrictHostKeyChecking=no -o ConnectTimeout={self.timeout}'}
                    )
                    
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(), 
                        timeout=self.timeout * 2
                    )
                    
                    if proc.returncode == 0:
                        # Success - found a valid username/repo combination
                        results['successful_usernames'].append({
                            'username': username,
                            'repository': f"{username}/{username}",
                            'url': repo_url
                        })
                    else:
                        results['failed_attempts'] += 1
                        
                except asyncio.TimeoutError:
                    results['failed_attempts'] += 1
                    results['errors'].append(f"Timeout testing {username}")
                except Exception as e:
                    results['failed_attempts'] += 1
                    results['errors'].append(f"Error testing {username}: {str(e)}")
        
        # Execute bruteforce attempts
        tasks = [test_username(username) for username in usernames]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
