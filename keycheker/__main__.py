#!/usr/bin/env python3

import argparse, sys, inspect


from utils.colors import red, end
from utils.read_file import read_key

from core.identify_key import *
from core.ssh.validate_ssh import *

from core import identify_key

from plugins.github.github_enum import *

def identify(args):
    key = read_key(args.filepath)

    # Iterate through all the functions in the identify_key.py and check for a valid key.
    function_names = [name for name, _ in inspect.getmembers(identify_key, inspect.isfunction)]
    for function_name in function_names:
        if hasattr(identify_key, function_name):
            function_to_call = getattr(identify_key, function_name)
            key_type = function_to_call(key)
    if key_type == None:
        print("😔 Cannot identify the key.")
    

def ssh(args):
    read_key(args.filepath)
    try:
        is_password_protected(args.filepath)
    except:
        chmod_400(args.filepath)
        is_password_protected(args.filepath)
        
    if args.generate_public_key == True:
        generate_public_key_with_comment(args.filepath)
    else:
        pass
    
    if args.enumerate_gh == True:
        if check_ssh_github_username(args.filepath):
            fetch_user_orgs()
    
    if args.brute_ssh_pass == True:
        print("Instructions to Bruteforce SSH Password")


def main():
    print('''%s
|   _      _ |_   _   _ |   _  ._
|< (/_ \/ (_ | | (/_ (_ |< (/_ | 
       /                         %s %s
---
''' % (red, '1.0.0', end))


    parser = argparse.ArgumentParser(
        prog="keychecker",
        description="Identifies the key and enumerates it for details.",
        epilog="For any issues/concerns reach out to keychecker@0xcardinal.com"
    )

    subparsers = parser.add_subparsers(title="subcommands", help="functionalities")

    identify_parser = subparsers.add_parser("identify", help="Identify the type of key.")
    identify_parser.add_argument('--input', help="Provide your key file.", dest='filepath', required=True)
    identify_parser.set_defaults(func=identify)

    ssh_parser = subparsers.add_parser("ssh", help="Enumerate using SSH key.")
    ssh_parser.add_argument('--input', help="Provide your public or private SSH key.", dest='filepath', required=True)
    ssh_parser.add_argument('--generate-public-key', help="Generates the associated public key.", dest='generate_public_key', action='store_true')
    ssh_parser.add_argument('--enumerate-gh', help="Enumerate GitHub using the SSH Private Key", dest='enumerate_gh', action='store_true')
    ssh_parser.add_argument('--bruteforce-ssh-pass-help', help="Provides you the command to bruteforce ssh key(s) password", dest='brute_ssh_pass', action='store_true')
    ssh_parser.add_argument('--bruteforce-gh-repo-help', help="Provides you the command to bruteforce GitHub repositories of the user", dest='brute_gh_repo', action='store_true')
    ssh_parser.set_defaults(func=ssh)

    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    if hasattr(args, 'func'):
        args.func(args)
    

if __name__ == '__main__':
    main()