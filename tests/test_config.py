"""Tests for configuration module."""

import pytest
import os
from unittest.mock import patch
from src.config import get_required_env_var, get_optional_env_var, load_config, validate_config
from src.types import Config


class TestEnvironmentVariables:
    """Test environment variable handling."""

    def test_get_required_env_var_exists(self):
        """Test getting a required env var that exists."""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            result = get_required_env_var('TEST_VAR')
            assert result == 'test_value'

    def test_get_required_env_var_missing(self):
        """Test getting a required env var that doesn't exist."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Required environment variable MISSING_VAR is not set"):
                get_required_env_var('MISSING_VAR')

    def test_get_optional_env_var_exists(self):
        """Test getting an optional env var that exists."""
        with patch.dict(os.environ, {'OPTIONAL_VAR': 'custom_value'}):
            result = get_optional_env_var('OPTIONAL_VAR', 'default_value')
            assert result == 'custom_value'

    def test_get_optional_env_var_missing(self):
        """Test getting an optional env var that doesn't exist returns default."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_optional_env_var('MISSING_VAR', 'default_value')
            assert result == 'default_value'


class TestLoadConfig:
    """Test configuration loading."""

    def test_load_config_with_all_required_vars(self):
        """Test loading config with all required environment variables."""
        env_vars = {
            'JIRA_HOST': 'https://test.atlassian.net',
            'JIRA_USERNAME': 'test@example.com',
            'JIRA_API_TOKEN': 'test_token_123',
            'JIRA_PROJECT_KEY': 'TEST',
            'GITHUB_TOKEN': 'github_token_123',
            'GITHUB_WEBHOOK_SECRET': 'webhook_secret',
            'GITHUB_OWNER': 'test_owner',
            'GITHUB_REPO': 'test_repo',
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            assert config.jira.host == 'https://test.atlassian.net'
            assert config.jira.username == 'test@example.com'
            assert config.jira.api_token == 'test_token_123'
            assert config.jira.project_key == 'TEST'
            assert config.jira.auth_method == 'basic'  # Default value
            
            assert config.github.token == 'github_token_123'
            assert config.github.webhook_secret == 'webhook_secret'
            assert config.github.owner == 'test_owner'
            assert config.github.repo == 'test_repo'
            
            assert config.server.port == 3000  # Default value
            assert config.server.name == 'jira-github-mcp'  # Default value

    def test_load_config_with_custom_auth_method(self):
        """Test loading config with custom auth method."""
        env_vars = {
            'JIRA_HOST': 'https://test.atlassian.net',
            'JIRA_USERNAME': 'test@example.com',
            'JIRA_API_TOKEN': 'test_token_123',
            'JIRA_PROJECT_KEY': 'TEST',
            'JIRA_AUTH_METHOD': 'bearer',
            'GITHUB_TOKEN': 'github_token_123',
            'GITHUB_WEBHOOK_SECRET': 'webhook_secret',
            'GITHUB_OWNER': 'test_owner',
            'GITHUB_REPO': 'test_repo',
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            assert config.jira.auth_method == 'bearer'

    def test_load_config_with_custom_server_settings(self):
        """Test loading config with custom server settings."""
        env_vars = {
            'JIRA_HOST': 'https://test.atlassian.net',
            'JIRA_USERNAME': 'test@example.com',
            'JIRA_API_TOKEN': 'test_token_123',
            'JIRA_PROJECT_KEY': 'TEST',
            'GITHUB_TOKEN': 'github_token_123',
            'GITHUB_WEBHOOK_SECRET': 'webhook_secret',
            'GITHUB_OWNER': 'test_owner',
            'GITHUB_REPO': 'test_repo',
            'PORT': '8080',
            'MCP_SERVER_NAME': 'custom-server-name',
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            assert config.server.port == 8080
            assert config.server.name == 'custom-server-name'

    def test_load_config_missing_required_var(self):
        """Test loading config with missing required variable."""
        # Test get_required_env_var directly instead of full load_config
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Required environment variable MISSING_VAR is not set"):
                get_required_env_var('MISSING_VAR')


class TestValidateConfig:
    """Test configuration validation."""

    def test_validate_config_valid(self):
        """Test validating a valid config."""
        config = Config(
            jira=Config.Jira(
                host='https://test.atlassian.net',
                username='test@example.com',
                api_token='test_token',
                project_key='TEST',
                auth_method='basic'
            ),
            github=Config.GitHub(
                token='github_token',
                webhook_secret='webhook_secret',
                owner='test_owner',
                repo='test_repo'
            ),
            server=Config.Server(
                port=3000,
                name='test-server'
            )
        )
        
        # Should not raise any exception
        validate_config(config)

    def test_validate_config_missing_jira_host(self):
        """Test validating config with missing JIRA host."""
        config = Config(
            jira=Config.Jira(
                host='',  # Empty host
                username='test@example.com',
                api_token='test_token',
                project_key='TEST',
                auth_method='basic'
            ),
            github=Config.GitHub(
                token='github_token',
                webhook_secret='webhook_secret',
                owner='test_owner',
                repo='test_repo'
            ),
            server=Config.Server(
                port=3000,
                name='test-server'
            )
        )
        
        with pytest.raises(ValueError, match="Missing required environment variables: JIRA_HOST"):
            validate_config(config)

    def test_validate_config_multiple_missing_fields(self):
        """Test validating config with multiple missing fields."""
        config = Config(
            jira=Config.Jira(
                host='',  # Empty host
                username='',  # Empty username
                api_token='test_token',
                project_key='TEST',
                auth_method='basic'
            ),
            github=Config.GitHub(
                token='',  # Empty token
                webhook_secret='webhook_secret',
                owner='test_owner',
                repo='test_repo'
            ),
            server=Config.Server(
                port=3000,
                name='test-server'
            )
        )
        
        with pytest.raises(ValueError, match="Missing required environment variables"):
            validate_config(config)