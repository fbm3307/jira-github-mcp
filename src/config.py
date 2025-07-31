"""Configuration management for Jira-GitHub MCP server."""

import os
from typing import Optional
from dotenv import load_dotenv
from .types import Config


def get_required_env_var(name: str) -> str:
    """Get a required environment variable."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Required environment variable {name} is not set")
    return value


def get_optional_env_var(name: str, default: str) -> str:
    """Get an optional environment variable with a default value."""
    return os.getenv(name, default)


def load_config() -> Config:
    """Load configuration from environment variables."""
    # Load environment variables from .env file if it exists
    load_dotenv()

    # Create Config instance
    config = Config(
        jira=Config.Jira(
            host=get_required_env_var('JIRA_HOST'),
            username=get_required_env_var('JIRA_USERNAME'),
            api_token=get_required_env_var('JIRA_API_TOKEN'),
            project_key=get_required_env_var('JIRA_PROJECT_KEY'),
            auth_method=get_optional_env_var('JIRA_AUTH_METHOD', 'basic'),
        ),
        github=Config.GitHub(
            token=get_required_env_var('GITHUB_TOKEN'),
            webhook_secret=get_required_env_var('GITHUB_WEBHOOK_SECRET'),
            owner=get_required_env_var('GITHUB_OWNER'),
            repo=get_required_env_var('GITHUB_REPO'),
        ),
        server=Config.Server(
            port=int(get_optional_env_var('PORT', '3000')),
            name=get_optional_env_var('MCP_SERVER_NAME', 'jira-github-mcp'),
        ),
    )

    return config


def validate_config(config: Config) -> None:
    """Validate that all required configuration is present."""
    required_fields = [
        (config.jira.host, "JIRA_HOST"),
        (config.jira.username, "JIRA_USERNAME"),
        (config.jira.api_token, "JIRA_API_TOKEN"),
        (config.jira.project_key, "JIRA_PROJECT_KEY"),
        (config.github.token, "GITHUB_TOKEN"),
        (config.github.webhook_secret, "GITHUB_WEBHOOK_SECRET"),
        (config.github.owner, "GITHUB_OWNER"),
        (config.github.repo, "GITHUB_REPO"),
    ]

    missing_fields = [field for value, field in required_fields if not value]
    
    if missing_fields:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_fields)}"
        )


# Global config instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global config
    if config is None:
        config = load_config()
        validate_config(config)
    return config 