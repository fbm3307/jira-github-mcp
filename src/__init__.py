"""Jira-GitHub MCP Server package."""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "MCP server that integrates Jira and GitHub for automated issue creation"

from .mcp_server import JiraGitHubMCPServer, run_mcp_server
from .webhook_server import WebhookServer, run_webhook_server
from .config import get_config
from .types import *

__all__ = [
    "JiraGitHubMCPServer",
    "WebhookServer", 
    "run_mcp_server",
    "run_webhook_server",
    "get_config",
] 