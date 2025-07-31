"""GitHub client for interacting with GitHub API."""

import logging
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from github import Github

from .types import (
    GitHubPullRequest, GitHubComment, GitHubUser, GitHubBranch, Config
)

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, config: Config):
        """Initialize GitHub client with configuration."""
        self.config = config
        self.github = Github(config.github.token)
        self.repo = self.github.get_repo(f"{config.github.owner}/{config.github.repo}")

    async def get_pull_request(self, number: int) -> Optional[GitHubPullRequest]:
        """Get pull request by number."""
        try:
            pr = self.repo.get_pull(number)
            return self._transform_pull_request(pr)
        except Exception as error:
            logger.error(f"Error fetching PR #{number}: {error}")
            return None

    async def get_all_pull_requests(self, state: str = "all") -> List[GitHubPullRequest]:
        """Get all pull requests."""
        try:
            prs = self.repo.get_pulls(state=state)
            return [self._transform_pull_request(pr) for pr in prs]
        except Exception as error:
            logger.error(f"Error fetching pull requests: {error}")
            raise

    async def get_pull_request_comments(self, number: int) -> List[GitHubComment]:
        """Get comments for a pull request."""
        try:
            pr = self.repo.get_pull(number)
            # Get issue comments (these are the ones shown in the PR conversation)
            issue = self.repo.get_issue(number)
            comments = issue.get_comments()
            
            return [
                GitHubComment(
                    id=comment.id,
                    body=comment.body,
                    user=GitHubUser(login=comment.user.login) if comment.user else None,
                    created_at=comment.created_at,
                    pull_request_number=number
                )
                for comment in comments
            ]
        except Exception as error:
            logger.error(f"Error fetching comments for PR #{number}: {error}")
            raise

    async def add_comment(self, number: int, body: str) -> GitHubComment:
        """Add a comment to a pull request."""
        try:
            issue = self.repo.get_issue(number)
            comment = issue.create_comment(body)
            
            return GitHubComment(
                id=comment.id,
                body=comment.body,
                user=GitHubUser(login=comment.user.login) if comment.user else None,
                created_at=comment.created_at,
                pull_request_number=number
            )
        except Exception as error:
            logger.error(f"Error adding comment to PR #{number}: {error}")
            raise

    def is_create_jira_comment(self, comment: str) -> bool:
        """Check if a comment contains a request to create a Jira issue."""
        triggers = [
            r'create\s+jira',
            r'make\s+jira',
            r'new\s+jira',
            r'jira\s+issue',
            r'create\s+issue',
            r'create\s+ticket'
        ]
        
        comment_lower = comment.lower()
        return any(re.search(trigger, comment_lower) for trigger in triggers)

    def extract_jira_details(
        self, 
        comment: str, 
        pr_title: str, 
        pr_body: Optional[str] = None,
        pr_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Extract Jira creation details from comment."""
        # Try to extract custom summary from comment
        summary_match = re.search(r'summary[:\s]+([^\n\r]+)', comment, re.IGNORECASE)
        type_match = re.search(r'type[:\s]+(bug|task|story|epic)', comment, re.IGNORECASE)
        labels_match = re.search(r'labels?[:\s]+([^\n\r]+)', comment, re.IGNORECASE)

        # Determine summary
        summary = summary_match.group(1).strip() if summary_match else pr_title
        if not summary_match:
            summary = f"[GitHub PR] {pr_title}"

        # Determine issue type
        issue_type = type_match.group(1).title() if type_match else "Task"

        # Determine labels
        labels = ["github-pr"]
        if labels_match:
            custom_labels = [label.strip() for label in labels_match.group(1).split(',')]
            labels.extend(custom_labels)

        # Build description
        description_parts = ["Created from GitHub Pull Request\n"]
        
        if pr_number:
            pr_url = self._get_pr_url(pr_number)
            description_parts.append(f"**Original PR:** [#{pr_number} {pr_title}]({pr_url})\n")
        
        if pr_body:
            description_parts.append(f"**PR Description:**\n{pr_body}\n")
        
        description_parts.append(f"**Comment that triggered creation:**\n{comment}")
        
        description = "\n".join(description_parts)

        return {
            "summary": summary,
            "description": description,
            "issue_type": issue_type,
            "labels": labels
        }

    def _get_pr_url(self, number: int) -> str:
        """Generate PR URL."""
        return f"https://github.com/{self.config.github.owner}/{self.config.github.repo}/pull/{number}"

    def _transform_pull_request(self, pr) -> GitHubPullRequest:
        """Transform GitHub API response to our GitHubPullRequest dataclass."""
        return GitHubPullRequest(
            id=pr.id,
            number=pr.number,
            title=pr.title,
            body=pr.body,
            user=GitHubUser(login=pr.user.login) if pr.user else None,
            head=GitHubBranch(ref=pr.head.ref, sha=pr.head.sha) if pr.head else None,
            base=GitHubBranch(ref=pr.base.ref, sha=pr.base.sha) if pr.base else None,
            state=pr.state,
            created_at=pr.created_at,
            html_url=pr.html_url
        ) 