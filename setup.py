#!/usr/bin/env python3
"""
Setup script for KeyChecker.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "Readme.md").read_text()

# Read requirements
requirements = []
with open('requirements.txt') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            # Only include core dependencies, not dev dependencies
            if not any(dev_pkg in line for dev_pkg in ['pytest', 'black', 'flake8', 'mypy']):
                requirements.append(line)

setup(
    name="keychecker",
    version="1.0.0",
    author="KeyChecker Team",
    author_email="contact@keychecker.dev",
    description="A fast CLI to fingerprint SSH private keys and identify which Git hosting accounts they unlock",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cyfinoid/keychecker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0", 
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "keychecker=keychecker.cli:main",
        ],
    },
    keywords="ssh key fingerprint git github gitlab bitbucket security audit",
    project_urls={
        "Bug Reports": "https://github.com/cyfinoid/keychecker/issues",
        "Source": "https://github.com/cyfinoid/keychecker",
        "Documentation": "https://github.com/cyfinoid/keychecker#readme",
    },
)
