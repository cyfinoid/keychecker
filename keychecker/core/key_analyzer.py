"""
SSH key analysis and fingerprinting functionality.
"""

import os
import base64
import hashlib
from typing import Dict, Any, Optional, List
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, dsa, ec, ed25519


class SSHKeyAnalyzer:
    """Analyzes SSH private keys and extracts metadata."""

    DEPRECATED_ALGORITHMS = {"dsa", "ssh-dss"}
    INSECURE_RSA_SIZES = {512, 1024}

    def __init__(self) -> None:
        self.key_types = {
            "ssh-rsa": "rsa",
            "ssh-dss": "dsa",
            "ssh-ed25519": "ed25519",
            "ecdsa-sha2-nistp256": "ecdsa",
            "ecdsa-sha2-nistp384": "ecdsa",
            "ecdsa-sha2-nistp521": "ecdsa",
        }

    def analyze_key_file(self, key_path: str) -> Dict[str, Any]:
        """
        Analyze an SSH private key file and extract metadata.

        Args:
            key_path: Path to the SSH private key file

        Returns:
            Dictionary containing key analysis results
        """
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Key file not found: {key_path}")

        with open(key_path, "rb") as f:
            key_data = f.read()

        # Try to load the private key with different formats
        private_key = None
        passphrase_protected = False

        # Try different key loading methods
        loaders = [
            # OpenSSH format (most common for modern SSH keys)
            lambda data, pwd: serialization.load_ssh_private_key(data, password=pwd),
            # PEM format (traditional format)
            lambda data, pwd: serialization.load_pem_private_key(data, password=pwd),
            # DER format (less common)
            lambda data, pwd: serialization.load_der_private_key(data, password=pwd),
        ]

        for loader in loaders:
            try:
                # Try without passphrase first
                private_key = loader(key_data, None)
                break
            except TypeError:
                # Key requires passphrase
                passphrase_protected = True
                continue
            except ValueError:
                # Wrong format, try next loader
                continue
            except Exception:
                # Other error, try next loader
                continue  # nosec B112

        if private_key is None and passphrase_protected:
            # We can still analyze the key structure without decrypting
            return self._analyze_encrypted_key(key_data, key_path)

        if private_key is None:
            # Try to get more info about the key format
            key_data_str = key_data.decode("utf-8", errors="ignore")

            # Check if this might be a public key instead
            if any(
                key_data_str.strip().startswith(prefix)
                for prefix in ["ssh-rsa", "ssh-ed25519", "ecdsa-sha2-", "ssh-dss"]
            ):
                raise ValueError(
                    "This appears to be a public key file, not a private key. "
                    "Please provide the private key file "
                    "(usually without .pub extension)"
                )

            if "BEGIN OPENSSH PRIVATE KEY" in key_data_str:
                raise ValueError(
                    "OpenSSH private key detected but couldn't parse - "
                    "may be passphrase protected or corrupted"
                )
            elif "BEGIN" in key_data_str and "PRIVATE KEY" in key_data_str:
                raise ValueError(
                    "PEM private key detected but couldn't parse - "
                    "may be passphrase protected or corrupted"
                )
            elif "BEGIN" in key_data_str and "PUBLIC KEY" in key_data_str:
                raise ValueError(
                    "This appears to be a public key file, not a private key. "
                    "Please provide the private key file"
                )
            else:
                raise ValueError(
                    "File doesn't appear to contain a recognized private key format"
                )

        # Extract public key
        public_key = private_key.public_key()

        # Get key type and size
        key_info = self._get_key_info(private_key, public_key)

        # Generate public key string
        public_key_str = self._generate_public_key_string(public_key, key_info["type"])

        # Extract comment from public key file if it exists
        comment = self._extract_comment(key_path, public_key_str)

        # Generate fingerprints
        fingerprint_sha256 = self._generate_fingerprint(public_key_str, "sha256")
        fingerprint_md5 = self._generate_fingerprint(public_key_str, "md5")

        # Analyze security
        security_flags = self._analyze_security(key_info)

        # Extract insights from comment
        insights = self._extract_insights(comment)

        result = {
            "input": key_path,
            "key": {
                "type": key_info["type"],
                "bits": key_info.get("bits"),
                "passphrase": passphrase_protected,
                "algorithm": key_info.get("algorithm"),
                "curve": key_info.get("curve"),
            },
            "public_key": {
                "key_string": public_key_str,
                "fingerprint_sha256": fingerprint_sha256,
                "fingerprint_md5": fingerprint_md5,
                "comment": comment,
            },
            "security": security_flags,
            "insights": insights,
        }

        return result

    def _analyze_encrypted_key(self, key_data: bytes, key_path: str) -> Dict[str, Any]:
        """Analyze an encrypted private key without decrypting it."""
        # Basic analysis of encrypted key
        key_data_str = key_data.decode("utf-8", errors="ignore")

        # Determine key type from header
        key_type = "unknown"
        algorithm = "unknown"

        if "BEGIN OPENSSH PRIVATE KEY" in key_data_str:
            key_type = "openssh"
            # For OpenSSH format, we can sometimes extract more info from the public key
            # Try to find corresponding .pub file
            pub_path = f"{key_path}.pub"
            if os.path.exists(pub_path):
                try:
                    with open(pub_path, "r") as f:
                        pub_content = f.read().strip()
                        parts = pub_content.split(" ", 2)
                        if len(parts) >= 2:
                            algorithm = parts[0]
                            if algorithm.startswith("ssh-"):
                                key_type = self.key_types.get(algorithm, algorithm)
                except Exception:
                    # Failed to parse embedded public key, continue with detection
                    pass  # nosec B110
        elif "BEGIN RSA PRIVATE KEY" in key_data_str:
            key_type = "rsa"
            algorithm = "ssh-rsa"
        elif "BEGIN DSA PRIVATE KEY" in key_data_str:
            key_type = "dsa"
            algorithm = "ssh-dss"
        elif "BEGIN EC PRIVATE KEY" in key_data_str:
            key_type = "ecdsa"
            algorithm = "ecdsa-sha2-*"
        elif "BEGIN PRIVATE KEY" in key_data_str:
            # PKCS#8 format - could be any key type
            key_type = "pkcs8"

        # Try to extract public key info if available
        public_key_info = self._try_extract_public_key_info(key_path)

        return {
            "input": key_path,
            "key": {
                "type": key_type,
                "bits": public_key_info.get("bits"),
                "passphrase": True,
                "algorithm": algorithm,
            },
            "public_key": {
                "key_string": public_key_info.get("key_string"),
                "fingerprint_sha256": public_key_info.get("fingerprint_sha256"),
                "fingerprint_md5": public_key_info.get("fingerprint_md5"),
                "comment": public_key_info.get("comment"),
            },
            "security": {"encrypted": True},
            "insights": public_key_info.get("insights", {}),
        }

    def _try_extract_public_key_info(self, key_path: str) -> Dict[str, Any]:
        """Try to extract public key information from corresponding .pub file."""
        pub_path = f"{key_path}.pub"
        if not os.path.exists(pub_path):
            return {}

        try:
            with open(pub_path, "r") as f:
                pub_content = f.read().strip()
                parts = pub_content.split(" ", 2)
                if len(parts) < 2:
                    return {}

                algorithm = parts[0]
                comment = parts[2] if len(parts) >= 3 else None

                # Generate fingerprints
                fingerprint_sha256 = self._generate_fingerprint(pub_content, "sha256")
                fingerprint_md5 = self._generate_fingerprint(pub_content, "md5")

                # Extract insights from comment
                insights = self._extract_insights(comment)

                # Estimate key size from algorithm
                bits = None
                if algorithm == "ssh-rsa":
                    # For RSA, we could decode the key data to get exact size
                    # but for now, assume common sizes
                    bits = 2048  # Most common
                elif algorithm == "ssh-ed25519":
                    bits = 256
                elif "ecdsa" in algorithm:
                    if "nistp256" in algorithm:
                        bits = 256
                    elif "nistp384" in algorithm:
                        bits = 384
                    elif "nistp521" in algorithm:
                        bits = 521

                return {
                    "key_string": pub_content,
                    "fingerprint_sha256": fingerprint_sha256,
                    "fingerprint_md5": fingerprint_md5,
                    "comment": comment,
                    "insights": insights,
                    "bits": bits,
                }

        except Exception:
            return {}

    def _get_key_info(self, private_key: Any, public_key: Any) -> Dict[str, Any]:
        """Extract key type and size information."""
        if isinstance(private_key, rsa.RSAPrivateKey):
            return {"type": "rsa", "bits": private_key.key_size, "algorithm": "ssh-rsa"}
        elif isinstance(private_key, dsa.DSAPrivateKey):
            return {"type": "dsa", "bits": private_key.key_size, "algorithm": "ssh-dss"}
        elif isinstance(private_key, ed25519.Ed25519PrivateKey):
            return {"type": "ed25519", "bits": 256, "algorithm": "ssh-ed25519"}
        elif isinstance(private_key, ec.EllipticCurvePrivateKey):
            curve_name = private_key.curve.name
            return {
                "type": "ecdsa",
                "bits": private_key.curve.key_size,
                "algorithm": f"ecdsa-sha2-{curve_name}",
                "curve": curve_name,
            }
        else:
            return {"type": "unknown", "bits": None, "algorithm": "unknown"}

    def _generate_public_key_string(self, public_key: Any, key_type: str) -> str:
        """Generate SSH public key string."""
        # Serialize public key to SSH format
        ssh_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )
        return str(ssh_public_key.decode("utf-8").strip())

    def _extract_comment(self, key_path: str, public_key_str: str) -> Optional[str]:
        """Extract comment from public key file or public key string."""
        # Check if there's a corresponding .pub file
        pub_path = f"{key_path}.pub"
        if os.path.exists(pub_path):
            try:
                with open(pub_path, "r") as f:
                    pub_content = f.read().strip()
                    parts = pub_content.split(" ", 2)
                    if len(parts) >= 3:
                        return str(parts[2])
            except Exception:
                # Failed to read companion .pub file, return None
                pass  # nosec B110

        # Try to extract from the public key string itself
        parts = public_key_str.split(" ", 2)
        if len(parts) >= 3:
            return str(parts[2])

        return None

    def _generate_fingerprint(
        self, public_key_str: str, hash_type: str = "sha256"
    ) -> Optional[str]:
        """Generate SSH key fingerprint."""
        # Parse the public key
        parts = public_key_str.split(" ")
        if len(parts) < 2:
            return None

        try:
            key_data = base64.b64decode(parts[1])

            if hash_type == "sha256":
                digest = hashlib.sha256(key_data).digest()
                fingerprint = base64.b64encode(digest).decode("utf-8").rstrip("=")
                return f"SHA256:{fingerprint}"
            elif hash_type == "md5":
                # MD5 is used here for SSH key fingerprint compatibility, not security
                digest = hashlib.md5(
                    key_data, usedforsecurity=False
                ).digest()  # nosec B324
                fingerprint = ":".join(f"{b:02x}" for b in digest)
                return f"MD5:{fingerprint}"
        except Exception:
            # Fingerprint generation failed, return None to indicate unavailable
            pass  # nosec B110

        return None

    def _analyze_security(self, key_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze key security and flag issues."""
        flags: Dict[str, Any] = {"deprecated": False, "insecure": False, "warnings": []}

        key_type = key_info.get("type", "").lower()
        algorithm = key_info.get("algorithm", "").lower()
        bits = key_info.get("bits", 0)

        # Check for deprecated algorithms
        if (
            key_type in self.DEPRECATED_ALGORITHMS
            or algorithm in self.DEPRECATED_ALGORITHMS
        ):
            flags["deprecated"] = True
            flags["warnings"].append(f"Algorithm {key_type} is deprecated")

        # Check RSA key size
        if key_type == "rsa" and bits in self.INSECURE_RSA_SIZES:
            flags["insecure"] = True
            flags["warnings"].append(f"RSA key size {bits} is insecure")
        elif key_type == "rsa" and bits < 2048:
            flags["warnings"].append(
                f"RSA key size {bits} is below recommended 2048 bits"
            )

        return flags

    def _extract_insights(self, comment: Optional[str]) -> Dict[str, Any]:
        """Extract insights from SSH key comment."""
        insights: Dict[str, Any] = {}

        if not comment:
            return insights

        # Try to parse user@hostname format
        if "@" in comment:
            parts = comment.split("@", 1)
            if len(parts) == 2:
                insights["local_user"] = parts[0]
                insights["host"] = parts[1]

        # Look for IP addresses
        import re

        ip_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        ip_matches: List[str] = re.findall(ip_pattern, comment)
        if ip_matches:
            insights["ip_addresses"] = ip_matches

        # Store original comment
        insights["original_comment"] = comment

        return insights
