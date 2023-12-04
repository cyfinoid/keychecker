# validate_ssh.py ---
# Check if the SSH key is valid? (default)
# Check if the SSH key is password protected? (default)
    # Do we want to bruteforce the password? (--bruteforce-ssh-password)
# Fetch the public key and associated comment (default)

import os
import subprocess as sp

def chmod_400(key):
    os.chmod(key, 400)

def is_password_protected(key):
    return_code = sp.call(["ssh-keygen", "-y", "-P", "", "-f", key], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    if return_code != 0:
        print("😄 SSH key is password-protected")
    else:
        print("❗ SSH key is not Password-protected")

def generate_public_key_with_comment(filepath):
    try:
        output = sp.check_output(["ssh-keygen", "-yef", filepath], text=True)
        print("👉 Associated Public Key -")
        print(output)
    except sp.CalledProcessError as e:
        print(f"❌ Command failed with return code {e.returncode}")

