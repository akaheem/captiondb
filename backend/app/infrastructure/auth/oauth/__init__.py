"""
OAuth infrastructure adapters.

Each adapter is isolated and implements the OAuthProvider interface.
"""
from .google import GoogleOAuthAdapter
from .github import GitHubOAuthAdapter
from .apple import AppleOAuthAdapter
from .microsoft import MicrosoftOAuthAdapter
from .twitter import TwitterOAuthAdapter

__all__ = [
    "GoogleOAuthAdapter",
    "GitHubOAuthAdapter",
    "AppleOAuthAdapter",
    "MicrosoftOAuthAdapter",
    "TwitterOAuthAdapter",
]
