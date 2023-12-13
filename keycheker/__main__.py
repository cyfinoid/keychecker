#!/usr/bin/env python3

import argparse, sys
from enum import auto
import inspect
from types import SimpleNamespace


from utils.colors import red, end
from utils.read_file import read_key

from core.identify_key import *
from core.ssh.validate_ssh import *

from core import identify_key

from plugins.github.github_enum import *
from plugins.gitlab.gitlab_enum import *

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
        print("🙏 Please remove the password from the key. Ref - https://stackoverflow.com/questions/112396/how-do-i-remove-the-passphrase-for-the-ssh-key-without-having-to-create-a-new-ke")
        exit()
        
    if args.generate_public_key == True:
        generate_public_key_with_comment(args.filepath)
    
    if args.enumerate_gh == True:
        if check_ssh_github_username(args.filepath):
            user_orgs = fetch_github_user_orgs()

        if args.bruteforce == True:
            wordlist = args.inject_wordlist
            if wordlist == '':
                print("❌ Please provide a wordlist to bruteforce ❌")
                exit()
            github_repo_bruteforce(user_orgs[1], user_orgs[0], wordlist, args.filepath)

    if args.enumerate_gl == True:
        if check_ssh_gitlab_username(args.filepath):
            user_orgs = fetch_gitlab_user_groups()

        if args.bruteforce == True:
            wordlist = args.inject_wordlist
            if wordlist == '':
                print("❌ Please provide a wordlist to bruteforce ❌")
                exit()
            gitlab_repo_bruteforce(user_orgs[1], user_orgs[0], wordlist, args.filepath)
        



def interactive():
    args = SimpleNamespace()
    automated_command = ["python3 keychecker"]
    print("keychecker is used to find more details of the juicy secret keys that you found in the wild!\n")
    file_path = input("Enter the key file's absolute path: ")
    read_key(file_path)
    args.filepath = file_path
    print("\n")
    print("🫸 Identifying the key...")
    key_type = identify(args)
    if (key_type == 'ssh_priv_key' or key_type == 'ssh_pub_key'):
        automated_command.append(f"ssh --input {file_path}")
        generate_public_key = input("Do you want to generate the associated public key? (y/n): ")
        if(generate_public_key == 'y'):
            args.generate_public_key = True
            automated_command.append("--generate-public-key")
        else:
            args.generate_public_key = False

        enumerate_gh_gl = input("Do you want to know if the key is associated with Code Repositories? (github/gitlab) : ")
        if(enumerate_gh_gl == 'github'):
            args.enumerate_gh = True
            automated_command.append("--github")
        else:
            args.enumerate_gh = False
        
        if(enumerate_gh_gl == 'gitlab'):
            args.enumerate_gl = True
            automated_command.append("--gitlab")
        else:
            args.enumerate_gl = False

        if ((args.enumerate_gh == True) or (args.enumerate_gl == True)):
            bruteforce_private_repo = input("Do you want to enumerate private repositories? (y/n): ")
            if (bruteforce_private_repo == 'y'):
                try:
                    wordlist = input("Provide the absolute path for the fuzzing wordlist: ")
                    read_key(wordlist)
                    if(bruteforce_private_repo == 'y'): 
                        args.bruteforce = True
                        args.inject_wordlist = wordlist
                        automated_command.append(f"--bruteforce --wordlist {args.inject_wordlist}")
                except:
                    print("❌ Please provide a repository name wordlist to bruteforce the private repository ❌")
                    exit()

            else:
                args.bruteforce = False
                args.inject_wordlist = ''

        ssh(args)
        print(f"\n\n---\nGenerate automated searches using the given command for the desired outcome - ")
        print(*automated_command)


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
    ssh_parser.add_argument('--bruteforce', help="Provides you the command to bruteforce the intended names.", dest='bruteforce', action='store_true')
    ssh_parser.add_argument('--wordlist', help="Provide the absolute path for the fuzzing wordlist.", dest='inject_wordlist')
    ssh_parser.add_argument('--generate-public-key', help="Generates the associated public key.", dest='generate_public_key', action='store_true')
    ssh_parser.add_argument('--github', help="Enumerate GitHub using the SSH Private Key", dest='enumerate_gh', action='store_true')
    ssh_parser.add_argument('--gitlab', help="Enumerate GitLab using the SSH Private Key", dest='enumerate_gl', action='store_true')

    ssh_parser.set_defaults(func=ssh)

    args = parser.parse_args()

    if not any(vars(args).values()):
        interactive()

    if hasattr(args, 'func'):
        args.func(args)
    

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Keyboard Interrupt Encountered!')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)