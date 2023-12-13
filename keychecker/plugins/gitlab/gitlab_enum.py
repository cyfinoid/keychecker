import re, requests
import subprocess as sp

from utils.read_file import read_key


def check_ssh_gitlab_username(filepath):
    global extracted_username
    ssh_output = sp.check_output(["ssh", "-F", "/dev/null", "-i", filepath, "git@gitlab.com"], text=True, stderr=sp.PIPE)
    if ssh_output != "git@gitlab.com: Permission denied (publickey).":
        extracted_username = re.search(r"Welcome to GitLab, @([^!]+)!", ssh_output).group(1) if re.search(r"Welcome to GitLab, @([^!]+)!", ssh_output) else ""
        if extracted_username == "":
            print("❌ No GitLab username found associated with this key.")
            return False
        else:
            print("🤩 GitLab user found! Ref - ", end="")
            print(f"https://gitlab.com/{extracted_username}")
            return True

def fetch_gitlab_user_groups():

    # Fetch the user's GitHub profile page
    url = f'https://gitlab.com/users/{extracted_username}/groups.json'
    response = requests.get(url)

    if response.status_code == 200:
        # parse json group content
        json_data = response.json()
        html_content = json_data.get('html', '')
        decoded_content = html_content.encode('utf-8').decode('unicode-escape')

        # Use the regular expression to extract organization names
        group_names = re.findall(r'<a\s+class="group-name"[^>]*>([^<]+)</a>', decoded_content)
        print(f"👉 Public Groups {extracted_username} is a part of: ", end="")
        for org_name in group_names:
            print(org_name, end=" |")
        return [group_names, extracted_username]
    else:
        print(f"Failed to fetch the GitLab profile page. Status code: {response.status_code}")


# Bruteforce the repository (to find private repos) by the user specified wordlist.
def gitlab_repo_bruteforce(extracted_username, orgs, wordlist, key):
    read_key(key)
    PRIVATE_KEY=key
    read_key(wordlist)
    private_repos ={}

    print()

    # Fuzzing for private repositories
    with open(wordlist, "r") as wordlist_file:
        print(f"🏃 Fuzzing repositories for the {extracted_username}...", end="")
        temp = []
        for line in wordlist_file:
            line = line.strip()
            ssh_git_command = f'ssh -i {PRIVATE_KEY} -F /dev/null -o IdentitiesOnly=yes'
            env = {'GIT_SSH_COMMAND': ssh_git_command}
            result = sp.call(["git", "ls-remote", f"git@gitlab.com:{extracted_username}/{line}.git", "-q"], env=env, stdout=sp.PIPE, stderr=sp.PIPE)
            if result == 0:
                temp.append(line)
        private_repos[extracted_username] = temp
        print("Done.")

    with open(wordlist, "r") as wordlist_file:
        for org in orgs:
            print(f"🏃 Fuzzing repositories for the {org}...", end="")
            temp = []
            for line in wordlist_file:
                line = line.strip()
                ssh_git_command = f'ssh -i {PRIVATE_KEY} -F /dev/null -o IdentitiesOnly=yes'
                env = {'GIT_SSH_COMMAND': ssh_git_command}
                result = sp.call(["git", "ls-remote", f"git@gitlab.com:{org}/{line}.git", "-q"], env=env, stdout=sp.PIPE, stderr=sp.PIPE)
                if result == 0:
                    temp.append(line)
            private_repos[org] = temp
            print("Done.")
    

    print("----- Private Repositories - ", end="")
    print(private_repos)