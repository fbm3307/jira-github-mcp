"""Type definitions for Jira-GitHub MCP server."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class IssueType(str, Enum):
    """Jira issue types."""
    BUG = "Bug"
    TASK = "Task"
    STORY = "Story"
    EPIC = "Epic"


class Priority(str, Enum):
    """Jira issue priorities."""
    HIGHEST = "Highest"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    LOWEST = "Lowest"


class PRState(str, Enum):
    """GitHub PR states."""
    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


@dataclass
class JiraStatus:
    """Jira issue status information."""
    name: str
    category_key: str


@dataclass
class JiraIssueType:
    """Jira issue type information."""
    name: str


@dataclass
class JiraProject:
    """Jira project information."""
    key: str
    name: str


@dataclass
class JiraUser:
    """Jira user information."""
    display_name: str
    email_address: str


@dataclass
class JiraIssue:
    """Jira issue representation."""
    id: str
    key: str
    summary: str
    description: Optional[str] = None
    status: Optional[JiraStatus] = None
    issue_type: Optional[JiraIssueType] = None
    project: Optional[JiraProject] = None
    assignee: Optional[JiraUser] = None
    reporter: Optional[JiraUser] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    labels: List[str] = field(default_factory=list)


@dataclass
class JiraBoard:
    """Jira board representation."""
    id: int
    name: str
    type: str
    project_key: Optional[str] = None


@dataclass
class GitHubUser:
    """GitHub user information."""
    login: str


@dataclass
class GitHubBranch:
    """GitHub branch information."""
    ref: str
    sha: str


@dataclass
class GitHubPullRequest:
    """GitHub pull request representation."""
    id: int
    number: int
    title: str
    body: Optional[str] = None
    user: Optional[GitHubUser] = None
    head: Optional[GitHubBranch] = None
    base: Optional[GitHubBranch] = None
    state: str = "open"
    created_at: Optional[datetime] = None
    html_url: Optional[str] = None


@dataclass
class GitHubComment:
    """GitHub comment representation."""
    id: int
    body: str
    user: Optional[GitHubUser] = None
    created_at: Optional[datetime] = None
    pull_request_number: Optional[int] = None


@dataclass
class IssueMatchResult:
    """Result of issue similarity matching."""
    score: float
    issue: JiraIssue
    matched_fields: List[str] = field(default_factory=list)


@dataclass
class CreateJiraIssueRequest:
    """Request to create a new Jira issue."""
    summary: str
    issue_type: str
    project_key: str
    description: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    priority: Optional[str] = None


@dataclass
class Config:
    """Application configuration."""
    
    @dataclass
    class Jira:
        host: str
        username: str
        api_token: str
        project_key: str
        auth_method: str = "basic"  # Default to basic auth for backward compatibility
    
    @dataclass
    class GitHub:
        token: str
        webhook_secret: str
        owner: str
        repo: str
    
    @dataclass
    class Server:
        port: int
        name: str
    
    jira: Jira
    github: GitHub
    server: Server


@dataclass
class WebhookPayload:
    """GitHub webhook payload."""
    action: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Result of processing a PR comment for Jira creation."""
    action: str  # 'created', 'found_similar', 'skipped'
    issue: Optional[JiraIssue] = None
    similarity: Optional[float] = None
    reason: Optional[str] = None 