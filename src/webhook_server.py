"""Webhook server for handling GitHub events."""

import asyncio
import hashlib
import hmac
import json
import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from .config import get_config
from .jira_client import JiraClient
from .github_client import GitHubClient
from .types import Config, CreateJiraIssueRequest, ProcessingResult

logger = logging.getLogger(__name__)


class WebhookServer:
    """Webhook server for handling GitHub events."""

    def __init__(self):
        """Initialize the webhook server."""
        self.config = get_config()
        self.jira_client = JiraClient(self.config)
        self.github_client = GitHubClient(self.config)
        self.app = FastAPI(title="Jira-GitHub MCP Webhook Server")
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up FastAPI routes."""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "ok", "timestamp": "2024-01-01T00:00:00Z"}

        @self.app.post("/webhook")
        async def github_webhook(request: Request, background_tasks: BackgroundTasks):
            """Handle GitHub webhook events."""
            try:
                # Get raw body and headers
                body = await request.body()
                signature = request.headers.get("x-hub-signature-256")
                event_type = request.headers.get("x-github-event")

                # Verify webhook signature
                if not self._verify_signature(body, signature):
                    raise HTTPException(status_code=401, detail="Invalid signature")

                # Parse payload
                payload = json.loads(body.decode("utf-8"))
                
                logger.info(f"Received GitHub webhook: {event_type}")

                # Process event in background
                background_tasks.add_task(
                    self._handle_webhook_event, event_type, payload
                )

                return {"success": True}

            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON payload")
            except Exception as error:
                logger.error(f"Webhook error: {error}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self.app.post("/trigger-jira-creation")
        async def manual_trigger(pr_number: int, comment: str):
            """Manual trigger endpoint for testing."""
            try:
                result = await self._process_pr_comment_for_jira(pr_number, comment)
                return result.__dict__
            except Exception as error:
                logger.error(f"Manual trigger error: {error}")
                raise HTTPException(status_code=500, detail=str(error))

    def _verify_signature(self, payload: bytes, signature: Optional[str]) -> bool:
        """Verify GitHub webhook signature."""
        if not signature:
            return False

        # Create HMAC signature
        mac = hmac.new(
            self.config.github.webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256
        )
        expected_signature = f"sha256={mac.hexdigest()}"

        return hmac.compare_digest(expected_signature, signature)

    async def _handle_webhook_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle different GitHub webhook events."""
        try:
            if event_type == "issue_comment":
                await self._handle_issue_comment(payload)
            elif event_type == "pull_request":
                await self._handle_pull_request(payload)
            else:
                logger.info(f"Unhandled webhook event: {event_type}")
        except Exception as error:
            logger.error(f"Error handling webhook event {event_type}: {error}")

    async def _handle_issue_comment(self, payload: Dict[str, Any]) -> None:
        """Handle issue comment events (includes PR comments)."""
        # Only handle new comments
        if payload["action"] != "created":
            return

        comment = payload["comment"]
        issue = payload["issue"]

        # Check if this is a PR comment
        if "pull_request" not in issue:
            return

        pr_number = issue["number"]
        comment_body = comment["body"]

        logger.info(f"Processing comment on PR #{pr_number}: {comment_body[:100]}...")

        # Check if comment requests Jira creation
        if self.github_client.is_create_jira_comment(comment_body):
            await self._process_pr_comment_for_jira(pr_number, comment_body)

    async def _handle_pull_request(self, payload: Dict[str, Any]) -> None:
        """Handle pull request events."""
        action = payload["action"]
        pr = payload["pull_request"]

        logger.info(f"PR #{pr['number']} {action}: {pr['title']}")

        # Auto-process PRs with certain labels
        if action == "opened":
            labels = [label["name"] for label in pr.get("labels", [])]
            if "needs-jira" in labels:
                comment = f"Auto-triggered: Create Jira issue for this PR\n\nType: Task\nSummary: {pr['title']}"
                await self._process_pr_comment_for_jira(pr["number"], comment)

    async def _process_pr_comment_for_jira(
        self, pr_number: int, comment: str, threshold: float = 0.7
    ) -> ProcessingResult:
        """Process PR comment for potential Jira creation."""
        try:
            # Check if comment is requesting Jira creation
            if not self.github_client.is_create_jira_comment(comment):
                logger.info("Comment does not request Jira creation")
                return ProcessingResult(
                    action="skipped", 
                    reason="No Jira creation request found"
                )

            # Get PR details
            pr = await self.github_client.get_pull_request(pr_number)
            if not pr:
                raise Exception(f"Pull request #{pr_number} not found")

            # Extract Jira details
            jira_details = self.github_client.extract_jira_details(
                comment, pr.title, pr.body, pr.number
            )

            # Ensure issues are synced
            if self.jira_client.needs_sync():
                logger.info("Syncing Jira issues...")
                await self.jira_client.sync_issues()

            # Search for similar existing issues
            search_text = f"{jira_details['summary']} {jira_details['description']}"
            similar_issues = self.jira_client.find_similar_issues(search_text, threshold)

            if similar_issues:
                best_match = similar_issues[0]
                
                logger.info(
                    f"Found similar issue: {best_match.issue.key} "
                    f"({best_match.score * 100:.1f}% similarity)"
                )
                
                # Add comment to PR about existing issue
                await self.github_client.add_comment(
                    pr_number,
                    f"🔍 **Found similar existing Jira issue:**\n\n"
                    f"[{best_match.issue.key}]({self.config.jira.host}/browse/{best_match.issue.key}) - {best_match.issue.summary}\n\n"
                    f"**Similarity score:** {best_match.score * 100:.1f}%\n"
                    f"**Matched fields:** {', '.join(best_match.matched_fields)}\n\n"
                    f"Please check if this existing issue covers your request before creating a new one."
                )

                return ProcessingResult(
                    action="found_similar",
                    issue=best_match.issue,
                    similarity=best_match.score
                )

            # No similar issues found, create new one
            logger.info("Creating new Jira issue...")
            request = CreateJiraIssueRequest(
                summary=jira_details["summary"],
                description=jira_details["description"],
                issue_type=jira_details["issue_type"],
                project_key=self.config.jira.project_key,
                labels=jira_details["labels"],
            )
            
            new_issue = await self.jira_client.create_issue(request)

            # Add comment to PR about created issue
            await self.github_client.add_comment(
                pr_number,
                f"✅ **Created Jira issue:**\n\n"
                f"[{new_issue.key}]({self.config.jira.host}/browse/{new_issue.key}) - {new_issue.summary}\n\n"
                f"**Type:** {new_issue.issue_type.name if new_issue.issue_type else 'Unknown'}\n"
                f"**Labels:** {', '.join(new_issue.labels) if new_issue.labels else 'None'}"
            )

            logger.info(f"Created Jira issue: {new_issue.key}")

            return ProcessingResult(action="created", issue=new_issue)

        except Exception as error:
            logger.error(f"Error processing PR comment for Jira: {error}")
            
            # Add error comment to PR
            try:
                await self.github_client.add_comment(
                    pr_number,
                    f"❌ **Error creating Jira issue:**\n\n"
                    f"{str(error)}\n\n"
                    f"Please check the server logs or try again later."
                )
            except Exception as comment_error:
                logger.error(f"Failed to add error comment: {comment_error}")

            raise error

    async def start(self) -> None:
        """Start the webhook server."""
        # Initial sync of Jira issues
        try:
            await self.jira_client.sync_issues()
            logger.info("Initial Jira sync completed")
        except Exception as error:
            logger.error(f"Failed to sync Jira issues on startup: {error}")

        logger.info(f"Webhook server starting on port {self.config.server.port}")
        logger.info(f"Webhook URL: http://localhost:{self.config.server.port}/webhook")

        # Start the server
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.config.server.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


async def run_webhook_server() -> None:
    """Run the webhook server."""
    server = WebhookServer()
    await server.start() 