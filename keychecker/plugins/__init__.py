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
from .assembla import AssemblaProvider
from .azuredevops import AzureDevOpsProvider
from .boltic import BolticProvider
from .dataops import DataOpsProvider
from .framagit import FramagitProvider
from .gitverse import GitVerseProvider
from .launchpad import LaunchpadProvider
from .notabug import NotABugProvider
from .sourcehut import SourceHutProvider

__all__ = [
    "BaseGitProvider",
    "GitHubProvider",
    "GitLabProvider",
    "GitLabSelfHostedProvider",
    "BitbucketProvider",
    "CodebergProvider",
    "GiteaProvider",
    "HuggingFaceProvider",
    "AssemblaProvider",
    "AzureDevOpsProvider",
    "BolticProvider",
    "DataOpsProvider",
    "FramagitProvider",
    "GitVerseProvider",
    "LaunchpadProvider",
    "NotABugProvider",
    "SourceHutProvider",
]
