"""Tests for authentication module."""

import pytest
import base64
from src.auth import (
    AuthenticatorBase,
    BasicAuthenticator,
    BearerAuthenticator,
    create_authenticator
)


class TestBasicAuthenticator:
    """Test BasicAuthenticator class."""

    def test_basic_auth_valid_credentials(self):
        """Test basic auth with valid credentials."""
        username = "test_user"
        password = "test_password"
        auth = BasicAuthenticator(username, password)
        
        headers = auth.get_headers()
        
        # Verify the Authorization header is present
        assert "Authorization" in headers
        
        # Verify it starts with "Basic "
        auth_header = headers["Authorization"]
        assert auth_header.startswith("Basic ")
        
        # Verify the encoded credentials are correct
        encoded_part = auth_header.replace("Basic ", "")
        decoded = base64.b64decode(encoded_part).decode("utf-8")
        assert decoded == f"{username}:{password}"

    def test_basic_auth_empty_username(self):
        """Test basic auth with empty username raises error."""
        with pytest.raises(ValueError, match="Basic authentication requires both username and password"):
            BasicAuthenticator("", "password")

    def test_basic_auth_empty_password(self):
        """Test basic auth with empty password raises error."""
        with pytest.raises(ValueError, match="Basic authentication requires both username and password"):
            BasicAuthenticator("username", "")

    def test_basic_auth_none_values(self):
        """Test basic auth with None values raises error."""
        with pytest.raises(ValueError, match="Basic authentication requires both username and password"):
            BasicAuthenticator(None, "password")
        
        with pytest.raises(ValueError, match="Basic authentication requires both username and password"):
            BasicAuthenticator("username", None)


class TestBearerAuthenticator:
    """Test BearerAuthenticator class."""

    def test_bearer_auth_valid_token(self):
        """Test bearer auth with valid token."""
        token = "test_bearer_token_123"
        auth = BearerAuthenticator(token)
        
        headers = auth.get_headers()
        
        # Verify the Authorization header is present
        assert "Authorization" in headers
        
        # Verify it's formatted correctly
        assert headers["Authorization"] == f"Bearer {token}"

    def test_bearer_auth_empty_token(self):
        """Test bearer auth with empty token raises error."""
        with pytest.raises(ValueError, match="Bearer authentication requires a token"):
            BearerAuthenticator("")

    def test_bearer_auth_none_token(self):
        """Test bearer auth with None token raises error."""
        with pytest.raises(ValueError, match="Bearer authentication requires a token"):
            BearerAuthenticator(None)


class TestCreateAuthenticator:
    """Test create_authenticator factory function."""

    def test_create_basic_authenticator(self):
        """Test creating basic authenticator."""
        username = "test_user"
        api_token = "test_token"
        
        auth = create_authenticator(username, api_token, "basic")
        
        assert isinstance(auth, BasicAuthenticator)
        headers = auth.get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

    def test_create_bearer_authenticator(self):
        """Test creating bearer authenticator."""
        api_token = "test_bearer_token"
        
        auth = create_authenticator("unused", api_token, "bearer")
        
        assert isinstance(auth, BearerAuthenticator)
        headers = auth.get_headers()
        assert headers["Authorization"] == f"Bearer {api_token}"

    def test_create_authenticator_default_method(self):
        """Test creating authenticator with default method (basic)."""
        username = "test_user"
        api_token = "test_token"
        
        auth = create_authenticator(username, api_token)  # No method specified
        
        assert isinstance(auth, BasicAuthenticator)

    def test_create_authenticator_invalid_method(self):
        """Test creating authenticator with invalid method raises error."""
        with pytest.raises(ValueError, match="Unknown authentication method: invalid"):
            create_authenticator("user", "token", "invalid")

    def test_create_basic_authenticator_missing_username(self):
        """Test creating basic authenticator with missing username."""
        with pytest.raises(ValueError, match="Basic authentication requires both username and api_token"):
            create_authenticator(None, "token", "basic")

    def test_create_basic_authenticator_missing_token(self):
        """Test creating basic authenticator with missing token."""
        with pytest.raises(ValueError, match="Basic authentication requires both username and api_token"):
            create_authenticator("user", None, "basic")

    def test_create_bearer_authenticator_missing_token(self):
        """Test creating bearer authenticator with missing token."""
        with pytest.raises(ValueError, match="Bearer authentication requires an api_token"):
            create_authenticator("user", None, "bearer")


class TestAuthenticatorBase:
    """Test AuthenticatorBase abstract class."""

    def test_cannot_instantiate_base_class(self):
        """Test that AuthenticatorBase cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AuthenticatorBase()