def id_ssh(key):
    key_string = key.strip()
    
    if key_string.startswith("-----BEGIN RSA PRIVATE KEY-----") or \
       key_string.startswith("-----BEGIN OPENSSH PRIVATE KEY-----") or \
       key_string.startswith("-----BEGIN ED25519 PRIVATE KEY-----") or \
       key_string.startswith("-----BEGIN EC PRIVATE KEY-----") or \
       key_string.startswith("-----BEGIN DSA PRIVATE KEY-----"):
        print("👉 SSH Private Key")
        return "ssh_priv_key"
    
    if key_string.startswith("ssh-rsa") or \
       key_string.startswith("ssh-ed25519") or \
       key_string.startswith("ecdsa-sha2-nistp256") or \
       key_string.startswith("ssh-dss") or \
       key_string.startswith("ssh-x25519") or \
       key_string.startswith("ssh-rsa-cert-v01@openssh.com") or \
       key_string.startswith("ssh-ed25519-cert-v01@openssh.com"):
        print("👉 SSH Public Key")
        return "ssh_pub_key"
