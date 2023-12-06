#!/usr/bin/env python3

import argparse
import inspect
from types import SimpleNamespace


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
            return key_type
    if key_type == None:
        print("😔 Cannot identify the key.")
        return None
    

def ssh(args):
    read_key(args.filepath)
    user_orgs = []
    if(is_password_protected(args.filepath) == True):
        print("🙏 Please remove the password from the file. Ref - <insert-link-here>")
        exit()
        
    if args.generate_public_key == True:
        generate_public_key_with_comment(args.filepath)
    
    if args.enumerate_gh == True:
        if check_ssh_github_username(args.filepath):
            user_orgs = fetch_user_orgs()
    # user_orgs = fetch_user_orgs()
    # print(user_orgs)

    if args.brute_gh_repo == True:
        # user_orgs = fetch_user_orgs()
        # print(user_orgs)
        wordlist = "/Users/cardinal/wordlist.txt"
        github_repo_bruteforce(user_orgs[1], user_orgs[0], wordlist, args.filepath)

    
    # if args.brute_ssh_pass == True:
    #     print("Instructions to Bruteforce SSH Password")


def interactive():
    args = SimpleNamespace()

    print("keychecker is used to find more details of the juicy secret keys that you found in the wild!\n")
    file_path = input("Enter the key file's absolute path: ")
    args.filepath = file_path

    generate_public_key = input("Do you want to generate the associated public key? (y/n): ")
    if(generate_public_key == 'y'):
        args.generate_public_key = True
    else:
        args.generate_public_key = False
        

    enumerate_github = input("Do you want to know if the key is associated with GitHub? (y/n): ")
    if(enumerate_github == 'y'):
        args.enumerate_gh = True
    else:
        args.enumerate_gh = False

    if (args.enumerate_gh == True):
        bruteforce_private_repo = input("Do you want to enumerate private repositories? (y/n): ")
        if(bruteforce_private_repo == 'y'): 
            args.brute_gh_repo = True

    

    print("\n")
    print("🫸 Identifying the key...")
    key_type = identify(args)
    if (key_type == 'ssh_priv_key' or key_type == 'ssh_pub_key'):
        ssh(args)


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
    ssh_parser.add_argument('--bruteforce-gh-repo', help="Provides you the command to bruteforce GitHub repositories of the user", dest='brute_gh_repo', action='store_true')
    ssh_parser.set_defaults(func=ssh)

    # args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    args = parser.parse_args()

    if not any(vars(args).values()):
        interactive()

    if hasattr(args, 'func'):
        args.func(args)
    

if __name__ == '__main__':
    main()