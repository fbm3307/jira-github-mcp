"""Jira client for interacting with Jira API."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from jira import JIRA
from fuzzywuzzy import fuzz
from fuzzywuzzy.process import extractBests

from .types import (
    JiraIssue, JiraBoard, CreateJiraIssueRequest, IssueMatchResult,
    JiraStatus, JiraIssueType, JiraProject, JiraUser, Config
)
from .auth import create_authenticator

logger = logging.getLogger(__name__)


class JiraClient:
    """Client for interacting with Jira API."""

    def __init__(self, config: Config):
        """Initialize Jira client with configuration."""
        self.config = config
        
        # Create authenticator using Jayrah's pattern
        try:
            authenticator = create_authenticator(
                username=config.jira.username,
                api_token=config.jira.api_token,
                auth_method=config.jira.auth_method
            )
        except ValueError as e:
            # Fall back to basic auth for unknown auth methods
            logger.warning(f"Invalid auth method '{config.jira.auth_method}', falling back to basic auth: {e}")
            authenticator = create_authenticator(
                username=config.jira.username,
                api_token=config.jira.api_token,
                auth_method="basic"
            )
        
        # Get auth headers and convert to basic_auth tuple for python-jira compatibility
        auth_headers = authenticator.get_headers()
        auth_header = auth_headers.get("Authorization", "")
        
        if auth_header.startswith("Basic "):
            # Use basic auth with python-jira
            self.jira = JIRA(
                server=config.jira.host,
                basic_auth=(config.jira.username, config.jira.api_token),
            )
        elif auth_header.startswith("Bearer "):
            # Use token auth for bearer authentication
            token = auth_header.replace("Bearer ", "")
            self.jira = JIRA(
                server=config.jira.host,
                token_auth=token,
            )
        else:
            # Fallback to basic auth for backward compatibility
            self.jira = JIRA(
                server=config.jira.host,
                basic_auth=(config.jira.username, config.jira.api_token),
            )
        
        self.issues: List[JiraIssue] = []
        self.last_sync: Optional[datetime] = None
        
        logger.info(f"Initialized Jira client with {config.jira.auth_method} authentication")

    async def sync_issues(self) -> None:
        """Sync all issues from Jira and cache them locally."""
        try:
            logger.info("Syncing Jira issues...")
            
            # Build JQL query
            jql = f"project = {self.config.jira.project_key} ORDER BY updated DESC"
            
            # Search for issues
            issues = self.jira.search_issues(
                jql,
                maxResults=1000,  # Adjust based on your needs
                fields=[
                    'id', 'key', 'summary', 'description', 'status',
                    'issuetype', 'project', 'assignee', 'reporter',
                    'created', 'updated', 'labels'
                ]
            )

            # Transform and cache issues
            self.issues = [self._transform_jira_issue(issue) for issue in issues]
            self.last_sync = datetime.now()
            
            logger.info(f"Synced {len(self.issues)} issues from Jira")
        except Exception as error:
            logger.error(f"Error syncing Jira issues: {error}")
            raise

    async def get_boards(self) -> List[JiraBoard]:
        """Get all boards for the project."""
        try:
            boards = self.jira.boards()
            project_boards = []
            
            for board in boards:
                # Filter boards by project key if location is available
                if hasattr(board, 'location') and board.location:
                    if board.location.get('projectKey') == self.config.jira.project_key:
                        project_boards.append(JiraBoard(
                            id=board.id,
                            name=board.name,
                            type=board.type,
                            project_key=board.location.get('projectKey')
                        ))
                else:
                    # If no location info, include all boards
                    project_boards.append(JiraBoard(
                        id=board.id,
                        name=board.name,
                        type=board.type,
                        project_key=None
                    ))
            
            return project_boards
        except Exception as error:
            logger.error(f"Error fetching Jira boards: {error}")
            raise

    def get_all_issues(self) -> List[JiraIssue]:
        """Get all cached issues."""
        return self.issues

    def find_similar_issues(self, search_text: str, threshold: float = 0.6) -> List[IssueMatchResult]:
        """Find similar issues based on text similarity."""
        if not self.issues:
            return []

        results = []
        
        for issue in self.issues:
            # Create searchable text from issue
            issue_text = f"{issue.summary} {issue.description or ''} {' '.join(issue.labels)}"
            
            # Calculate similarity scores for different fields
            summary_score = fuzz.token_sort_ratio(search_text.lower(), issue.summary.lower()) / 100
            description_score = 0
            if issue.description:
                description_score = fuzz.token_sort_ratio(search_text.lower(), issue.description.lower()) / 100
            
            labels_score = 0
            if issue.labels:
                labels_text = ' '.join(issue.labels)
                labels_score = fuzz.token_sort_ratio(search_text.lower(), labels_text.lower()) / 100

            # Weighted combined score
            combined_score = (summary_score * 0.7) + (description_score * 0.3) + (labels_score * 0.2)
            
            # Normalize to 0-1 range
            combined_score = min(combined_score, 1.0)
            
            if combined_score >= threshold:
                matched_fields = []
                if summary_score >= threshold:
                    matched_fields.append('summary')
                if description_score >= threshold:
                    matched_fields.append('description')
                if labels_score >= threshold:
                    matched_fields.append('labels')
                
                results.append(IssueMatchResult(
                    score=combined_score,
                    issue=issue,
                    matched_fields=matched_fields
                ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    async def create_issue(self, request: CreateJiraIssueRequest) -> JiraIssue:
        """Create a new Jira issue."""
        try:
            issue_data = {
                'project': {'key': request.project_key},
                'summary': request.summary,
                'description': request.description or '',
                'issuetype': {'name': request.issue_type},
                'labels': request.labels or [],
            }

            # Add optional fields
            if request.assignee:
                issue_data['assignee'] = {'name': request.assignee}
            
            if request.priority:
                issue_data['priority'] = {'name': request.priority}

            # Create the issue
            new_issue = self.jira.create_issue(fields=issue_data)
            
            # Fetch the created issue to get full details
            created_issue = self.jira.issue(new_issue.key)
            transformed_issue = self._transform_jira_issue(created_issue)
            
            # Add to our cache
            self.issues.insert(0, transformed_issue)
            
            logger.info(f"Created Jira issue: {new_issue.key}")
            return transformed_issue
        except Exception as error:
            logger.error(f"Error creating Jira issue: {error}")
            raise

    async def get_issue(self, key: str) -> Optional[JiraIssue]:
        """Get issue by key."""
        try:
            issue = self.jira.issue(key)
            return self._transform_jira_issue(issue)
        except Exception as error:
            logger.error(f"Error fetching issue {key}: {error}")
            return None

    def needs_sync(self) -> bool:
        """Check if sync is needed (older than 5 minutes)."""
        if not self.last_sync:
            return True
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        return self.last_sync < five_minutes_ago

    def _transform_jira_issue(self, issue) -> JiraIssue:
        """Transform Jira API response to our JiraIssue dataclass."""
        # Parse dates
        created = None
        updated = None
        if hasattr(issue.fields, 'created') and issue.fields.created:
            created = datetime.fromisoformat(issue.fields.created.replace('Z', '+00:00'))
        if hasattr(issue.fields, 'updated') and issue.fields.updated:
            updated = datetime.fromisoformat(issue.fields.updated.replace('Z', '+00:00'))

        # Extract status
        status = None
        if hasattr(issue.fields, 'status') and issue.fields.status:
            status = JiraStatus(
                name=issue.fields.status.name,
                category_key=issue.fields.status.statusCategory.key if hasattr(issue.fields.status, 'statusCategory') else 'unknown'
            )

        # Extract issue type
        issue_type = None
        if hasattr(issue.fields, 'issuetype') and issue.fields.issuetype:
            issue_type = JiraIssueType(name=issue.fields.issuetype.name)

        # Extract project
        project = None
        if hasattr(issue.fields, 'project') and issue.fields.project:
            project = JiraProject(
                key=issue.fields.project.key,
                name=issue.fields.project.name
            )

        # Extract assignee
        assignee = None
        if hasattr(issue.fields, 'assignee') and issue.fields.assignee:
            assignee = JiraUser(
                display_name=issue.fields.assignee.displayName,
                email_address=getattr(issue.fields.assignee, 'emailAddress', '')
            )

        # Extract reporter
        reporter = None
        if hasattr(issue.fields, 'reporter') and issue.fields.reporter:
            reporter = JiraUser(
                display_name=issue.fields.reporter.displayName,
                email_address=getattr(issue.fields.reporter, 'emailAddress', '')
            )

        return JiraIssue(
            id=issue.id,
            key=issue.key,
            summary=issue.fields.summary,
            description=getattr(issue.fields, 'description', None),
            status=status,
            issue_type=issue_type,
            project=project,
            assignee=assignee,
            reporter=reporter,
            created=created,
            updated=updated,
            labels=getattr(issue.fields, 'labels', []) or []
        ) 