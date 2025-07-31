"""Tests for JIRA client authentication integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.jira_client import JiraClient
from src.types import Config


class TestJiraClientAuthentication:
    """Test JiraClient authentication initialization."""

    def create_test_config(self, auth_method="basic"):
        """Helper to create test config."""
        return Config(
            jira=Config.Jira(
                host='https://test.atlassian.net',
                username='test@example.com',
                api_token='test_token_123',
                project_key='TEST',
                auth_method=auth_method
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

    @patch('src.jira_client.JIRA')
    def test_jira_client_basic_auth_initialization(self, mock_jira_class):
        """Test JiraClient initialization with basic auth."""
        mock_jira_instance = MagicMock()
        mock_jira_class.return_value = mock_jira_instance
        
        config = self.create_test_config("basic")
        client = JiraClient(config)
        
        # Verify JIRA was called with basic_auth
        mock_jira_class.assert_called_once_with(
            server='https://test.atlassian.net',
            basic_auth=('test@example.com', 'test_token_123')
        )
        
        assert client.config == config
        assert client.jira == mock_jira_instance

    @patch('src.jira_client.JIRA')
    def test_jira_client_bearer_auth_initialization(self, mock_jira_class):
        """Test JiraClient initialization with bearer auth."""
        mock_jira_instance = MagicMock()
        mock_jira_class.return_value = mock_jira_instance
        
        config = self.create_test_config("bearer")
        client = JiraClient(config)
        
        # Verify JIRA was called with token_auth
        mock_jira_class.assert_called_once_with(
            server='https://test.atlassian.net',
            token_auth='test_token_123'
        )
        
        assert client.config == config
        assert client.jira == mock_jira_instance

    @patch('src.jira_client.JIRA')
    def test_jira_client_invalid_auth_fallback(self, mock_jira_class):
        """Test JiraClient falls back to basic auth for invalid auth method."""
        mock_jira_instance = MagicMock()
        mock_jira_class.return_value = mock_jira_instance
        
        config = self.create_test_config("invalid_method")
        client = JiraClient(config)
        
        # Should fall back to basic auth
        mock_jira_class.assert_called_once_with(
            server='https://test.atlassian.net',
            basic_auth=('test@example.com', 'test_token_123')
        )

    @patch('src.jira_client.create_authenticator')
    @patch('src.jira_client.JIRA')
    def test_authenticator_creation_called_correctly(self, mock_jira_class, mock_create_auth):
        """Test that create_authenticator is called with correct parameters."""
        mock_auth = MagicMock()
        mock_auth.get_headers.return_value = {"Authorization": "Basic dGVzdEBleGFtcGxlLmNvbTp0ZXN0X3Rva2VuXzEyMw=="}
        mock_create_auth.return_value = mock_auth
        
        config = self.create_test_config("basic")
        client = JiraClient(config)
        
        # Verify create_authenticator was called with correct parameters
        mock_create_auth.assert_called_once_with(
            username='test@example.com',
            api_token='test_token_123',
            auth_method='basic'
        )

    @patch('src.jira_client.create_authenticator')
    @patch('src.jira_client.JIRA')
    def test_bearer_auth_header_processing(self, mock_jira_class, mock_create_auth):
        """Test that bearer auth headers are processed correctly."""
        mock_auth = MagicMock()
        mock_auth.get_headers.return_value = {"Authorization": "Bearer test_token_123"}
        mock_create_auth.return_value = mock_auth
        
        config = self.create_test_config("bearer")
        client = JiraClient(config)
        
        # Should use token_auth for bearer
        mock_jira_class.assert_called_once_with(
            server='https://test.atlassian.net',
            token_auth='test_token_123'
        )

    @patch('src.jira_client.logger')
    @patch('src.jira_client.JIRA')
    def test_authentication_logging(self, mock_jira_class, mock_logger):
        """Test that authentication method is logged."""
        config = self.create_test_config("bearer")
        client = JiraClient(config)
        
        # Verify logging was called
        mock_logger.info.assert_called_with("Initialized Jira client with bearer authentication")


class TestJiraClientMethods:
    """Test JiraClient methods work with different auth configurations."""

    def create_test_config(self, auth_method="basic"):
        """Helper to create test config."""
        return Config(
            jira=Config.Jira(
                host='https://test.atlassian.net',
                username='test@example.com',
                api_token='test_token_123',
                project_key='TEST',
                auth_method=auth_method
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

    @patch('src.jira_client.JIRA')
    def test_sync_issues_basic_auth(self, mock_jira_class):
        """Test sync_issues method with basic auth."""
        mock_jira_instance = MagicMock()
        mock_issue = MagicMock()
        mock_issue.id = "123"
        mock_issue.key = "TEST-123"
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = "Test Description"
        mock_issue.fields.status.name = "Open"
        mock_issue.fields.issuetype.name = "Task"
        mock_issue.fields.project.key = "TEST"
        mock_issue.fields.project.name = "Test Project"
        mock_issue.fields.assignee = None
        mock_issue.fields.reporter = None
        mock_issue.fields.created = "2024-01-01T00:00:00.000+0000"
        mock_issue.fields.updated = "2024-01-01T00:00:00.000+0000"
        mock_issue.fields.labels = []
        
        mock_jira_instance.search_issues.return_value = [mock_issue]
        mock_jira_class.return_value = mock_jira_instance
        
        config = self.create_test_config("basic")
        client = JiraClient(config)
        
        # This should work without authentication errors
        import asyncio
        asyncio.run(client.sync_issues())
        
        # Verify the JIRA search was called
        mock_jira_instance.search_issues.assert_called_once()
        assert len(client.issues) == 1