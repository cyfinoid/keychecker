"""
Tests for SSH key analyzer functionality.
"""

import pytest
import tempfile
import os
import warnings
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, dsa, ed25519

from keychecker.core.key_analyzer import SSHKeyAnalyzer


class TestSSHKeyAnalyzer:
    """Test cases for SSHKeyAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = SSHKeyAnalyzer()

    def test_analyze_rsa_key(self):
        """Test analysis of RSA private key."""
        # Generate a test RSA key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            f.write(pem)
            key_path = f.name

        try:
            # Analyze the key
            result = self.analyzer.analyze_key_file(key_path)

            # Verify results
            assert result["key"]["type"] == "rsa"
            assert result["key"]["bits"] == 2048
            assert result["key"]["passphrase"] is False
            assert result["public_key"]["fingerprint_sha256"] is not None
            assert result["public_key"]["key_string"] is not None

        finally:
            os.unlink(key_path)

    def test_analyze_ed25519_key(self):
        """Test analysis of Ed25519 private key."""
        # Generate a test Ed25519 key
        private_key = ed25519.Ed25519PrivateKey.generate()

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            f.write(pem)
            key_path = f.name

        try:
            # Analyze the key
            result = self.analyzer.analyze_key_file(key_path)

            # Verify results
            assert result["key"]["type"] == "ed25519"
            assert result["key"]["bits"] == 256
            assert result["key"]["passphrase"] is False
            assert result["public_key"]["fingerprint_sha256"] is not None
            assert result["public_key"]["key_string"] is not None

        finally:
            os.unlink(key_path)

    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        with pytest.raises(FileNotFoundError):
            self.analyzer.analyze_key_file("/nonexistent/key/file")

    def test_security_analysis_deprecated_dsa(self):
        """Test security analysis flags deprecated DSA keys."""
        # This is a mock test since generating DSA keys is more complex
        key_info = {"type": "dsa", "bits": 1024, "algorithm": "ssh-dss"}
        security = self.analyzer._analyze_security(key_info)

        assert security["deprecated"] is True
        assert len(security["warnings"]) > 0

    def test_security_analysis_insecure_rsa(self):
        """Test security analysis flags insecure RSA keys."""
        key_info = {"type": "rsa", "bits": 1024, "algorithm": "ssh-rsa"}
        security = self.analyzer._analyze_security(key_info)

        assert security["insecure"] is True
        assert len(security["warnings"]) > 0

    def test_extract_insights_from_comment(self):
        """Test extraction of insights from SSH key comment."""
        comment = "user@hostname"
        insights = self.analyzer._extract_insights(comment)

        assert insights["local_user"] == "user"
        assert insights["host"] == "hostname"
        assert insights["original_comment"] == comment

    def test_analyze_dsa_key_captures_deprecation_warning(self):
        """Test that CryptographyDeprecationWarning is consumed and reported."""
        # Generate a DSA key (deprecated algorithm in cryptography)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            private_key = dsa.generate_private_key(key_size=1024)

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            f.write(pem)
            key_path = f.name

        try:
            # Analyze with warnings captured by the tool
            from cryptography.utils import CryptographyDeprecationWarning

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                result = self.analyzer.analyze_key_file(key_path)

            # The deprecation warning must not leak to the caller
            assert not any(
                issubclass(w.category, CryptographyDeprecationWarning) for w in caught
            )
            # ...but must be reported inside the result
            assert result["key"]["type"] == "dsa"
            assert result["warnings"], "expected deprecation warning in result"
            assert any("deprecated" in w.lower() for w in result["warnings"])

        finally:
            os.unlink(key_path)

    def test_encrypted_pkcs8_pem_detected(self):
        """Test that OpenSSL PKCS#8 encrypted keys are detected as pkcs8."""
        key_data = (
            b"-----BEGIN ENCRYPTED PRIVATE KEY-----\n"
            b"MIHpBgsqhkiG9w0BBQ0wLwYK\n"
            b"-----END ENCRYPTED PRIVATE KEY-----\n"
        )
        result = self.analyzer._analyze_encrypted_key(key_data, "/tmp/fake_key")

        assert result["key"]["type"] == "pkcs8"
        assert result["key"]["passphrase"] is True
        assert result["warnings"] == []

    def test_rsa_key_has_empty_warnings(self):
        """Test that normal keys have no captured warnings."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            f.write(pem)
            key_path = f.name

        try:
            result = self.analyzer.analyze_key_file(key_path)
            assert result["warnings"] == []
        finally:
            os.unlink(key_path)
