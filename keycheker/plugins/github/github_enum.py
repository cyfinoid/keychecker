import re, requests
import subprocess as sp

from utils.read_file import read_key


def check_ssh_github_username(filepath):
    global extracted_username
    try:
        _ = sp.check_output(["ssh", "-F", "/dev/null", "-i", filepath, "git@github.com"], text=True, stderr=sp.PIPE)
    except sp.CalledProcessError as e:
        extracted_username = re.search(r"Hi ([^!]+)", e.stderr).group(1) if re.search(r"Hi ([^!]+)", e.stderr) else ""
        if extracted_username == "":
            print("No Github username found Associated with this key")
            return False
        else:
            print("🤩 GitHub user found! Ref - ", end="")
            print(f"https://github.com/{extracted_username}")
            return True

def fetch_user_orgs():

    # Fetch the user's GitHub profile page
    url = f'https://github.com/{extracted_username}'
    response = requests.get(url)

    if response.status_code == 200:
        # Use the regular expression to extract organization names
        organization_names = re.findall(r'data-hovercard-type="organization" data-hovercard-url="/orgs/([^/]+)/hovercard"', response.text)
        print(f"\t👉 Public Organizations {extracted_username} is a part of: ", end="")
        for org_name in organization_names:
            print(org_name, end="|")
    else:
        print(f"Failed to fetch the GitHub profile page. Status code: {response.status_code}")


# Bruteforce the repository (to find private repos) by the user specified wordlist.
def github_repo_bruteforce(extracted_username, orgs, wordlist, key):
    PRIVATE_KEY=key

    read_key(wordlist)

    public_repos = {}
    private_repos ={}

    # Get all public repositories of the user and the orgs.
    user_public_repo = requests.get(f"https://api.github.com/users/{extracted_username}/repos").json()
    user_public_repo = [repo["name"] for repo in user_public_repo]
    if not user_public_repo:
        print("❌ No public repositories for the user")
        public_repos[extracted_username]=[]
    else:
        public_repos[extracted_username]=user_public_repo

    for org in orgs:
        org_public_repo = requests.get(f"https://api.github.com/orgs/{org}/repos").json()
        org_public_repo = [repo["name"] for repo in org_public_repo]
        if not org_public_repo:
            print(f"❌ No public repositories for {org}")
            public_repos[org]=[]
        else:
            public_repos[org]=org_public_repo
    
    # Fuzzing for private repositories
    with open(wordlist, "r") as wordlist_file:
        print(f"🏃 Fuzzing repositories for the {extracted_username}...", end="")
        temp = []
        for line in wordlist_file:
            line = line.strip()
            result = sp.call([f"GIT_SSH_COMMAND='ssh -i {PRIVATE_KEY} -F /dev/null -o IdentitiesOnly=yes'", "git", "ls-remote", f"git@github.com:{extracted_username}/{line}.git", "-q"], stdout=sp.PIPE, stderr=sp.PIPE)
            if result == 0:
                temp.append(line)
        private_repos[extracted_username] = temp
        print("Done.")


        for org in orgs:
            print(f"🏃 Fuzzing repositories for the {org}...")
            temp = []
            for line in wordlist_file:
                line = line.strip()
                result = sp.call([f"GIT_SSH_COMMAND='ssh -i {PRIVATE_KEY} -F /dev/null -o IdentitiesOnly=yes'", "git", "ls-remote", f"git@github.com:{org}/{line}.git", "-q"], stdout=sp.PIPE, stderr=sp.PIPE)
                if result == 0:
                    temp.append(line)
            private_repos[org] = temp

    print(private_repos)
    print(public_repos)