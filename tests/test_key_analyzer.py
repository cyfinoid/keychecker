"""
Tests for SSH key analyzer functionality.
"""

import pytest
import tempfile
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519

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
