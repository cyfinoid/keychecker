import re, requests
import subprocess as sp

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


# def github_repo_bruteforce():
#     # GIT_SSH_COMMAND='ssh -i PRIVATE_KEY -o IdentitiesOnly=yes' git clone git@github.com:<org>/<REPO-BRUTEFORCE>.git
#     pass