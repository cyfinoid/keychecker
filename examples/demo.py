#!/usr/bin/env python3
"""
Demo script showing KeyChecker usage programmatically.
"""

import asyncio
import tempfile
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from keychecker.core.key_analyzer import SSHKeyAnalyzer
from keychecker.core.server_validator import ServerValidator
from keychecker.utils.output import OutputFormatter


async def demo():
    """Demonstrate KeyChecker functionality."""
    print("🔑 KeyChecker Demo")
    print("=" * 50)

    # Generate a demo Ed25519 key
    print("1. Generating demo Ed25519 key...")
    private_key = ed25519.Ed25519PrivateKey.generate()

    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".key") as f:
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        f.write(pem)
        key_path = f.name

    try:
        # Initialize components
        analyzer = SSHKeyAnalyzer()
        validator = ServerValidator(timeout=3)
        formatter = OutputFormatter()

        # Analyze the key
        print(f"2. Analyzing key: {key_path}")
        analysis_result = analyzer.analyze_key_file(key_path)

        print("3. Analysis Results:")
        print("-" * 30)
        output = formatter.format_analysis_result(analysis_result)
        print(output)

        # Note: We skip server validation and repository discovery in demo to avoid making actual network calls
        print("\n5. Demo completed successfully! ✅")
        print("\nTo test server validation, use:")
        print(f"keychecker -i {key_path} --validate github")
        print("\nTo test repository discovery, use:")
        print(
            f"keychecker -i {key_path} --discover-repos --server github --wordlist examples/sample_repo_names.txt"
        )

    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        # Clean up
        if os.path.exists(key_path):
            os.unlink(key_path)
            print(f"Cleaned up temporary key: {key_path}")


if __name__ == "__main__":
    asyncio.run(demo())
