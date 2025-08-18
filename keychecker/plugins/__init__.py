"""
Git hosting provider plugins for KeyChecker.
"""

from .base import BaseGitProvider
from .github import GitHubProvider
from .gitlab import GitLabProvider, GitLabSelfHostedProvider
from .bitbucket import BitbucketProvider
from .codeberg import CodebergProvider
from .gitea import GiteaProvider
from .huggingface import HuggingFaceProvider

__all__ = [
    "BaseGitProvider",
    "GitHubProvider",
    "GitLabProvider",
    "GitLabSelfHostedProvider",
    "BitbucketProvider",
    "CodebergProvider",
    "GiteaProvider",
    "HuggingFaceProvider",
]
