"""Authentication handlers for Jira API."""

import base64
from abc import ABC, abstractmethod
from typing import Dict

import logging

logger = logging.getLogger(__name__)


class AuthenticatorBase(ABC):
    """Base class for authentication handlers."""

    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""


class BearerAuthenticator(AuthenticatorBase):
    """Bearer token authentication."""

    def __init__(self, token: str):
        if not token:
            raise ValueError("Bearer authentication requires a token")
        self.token = token

    def get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


class BasicAuthenticator(AuthenticatorBase):
    """Basic authentication with username and password/token."""

    def __init__(self, username: str, password: str):
        if not username or not password:
            raise ValueError(
                "Basic authentication requires both username and password/token"
            )
        self.username = username
        self.password = password

    def get_headers(self) -> Dict[str, str]:
        auth_string = f"{self.username}:{self.password}"
        encoded_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {encoded_auth}"}


def create_authenticator(username: str, api_token: str, auth_method: str = "basic") -> AuthenticatorBase:
    """Factory function to create appropriate authenticator."""
    if auth_method == "basic":
        if username is None or api_token is None:
            raise ValueError(
                "Basic authentication requires both username and api_token"
            )
        return BasicAuthenticator(username, api_token)
    elif auth_method == "bearer":
        if api_token is None:
            raise ValueError(
                "Bearer authentication requires an api_token"
            )
        return BearerAuthenticator(api_token)
    else:
        raise ValueError(f"Unknown authentication method: {auth_method}")