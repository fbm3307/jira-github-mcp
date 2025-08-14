"""Webhook server for handling GitHub events."""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
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
        self.app = FastAPI(title="Jira-GitHub MCP Webhook Server", version="1.0.0")
        
        # Metrics tracking
        self.start_time = time.time()
        self.metrics = {
            "webhooks_received": 0,
            "jira_issues_created": 0,
            "similar_issues_found": 0,
            "duplicates_prevented": 0,
            "errors_encountered": 0,
            "last_webhook_time": None,
            "last_jira_sync": None,
        }
        
        self._setup_routes()

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime seconds into human readable string."""
        seconds = int(seconds)
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {remaining_seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {remaining_seconds}s"
        elif minutes > 0:
            return f"{minutes}m {remaining_seconds}s"
        else:
            return f"{remaining_seconds}s"

    def _setup_routes(self) -> None:
        """Set up FastAPI routes."""

        @self.app.get("/health")
        async def health_check():
            """Comprehensive health check endpoint."""
            current_time = datetime.now(timezone.utc)
            uptime_seconds = time.time() - self.start_time
            
            # Test Jira connectivity
            jira_status = "unknown"
            jira_error = None
            try:
                # Quick test - get issue count from cache
                jira_issues = self.jira_client.get_all_issues()
                jira_status = "healthy" if len(jira_issues) >= 0 else "no_data"
            except Exception as e:
                jira_status = "error"
                jira_error = str(e)[:100]  # Truncate long error messages
            
            # Test GitHub connectivity  
            github_status = "unknown"
            github_error = None
            try:
                # Basic config validation for GitHub
                if hasattr(self.config.github, 'token') and self.config.github.token:
                    github_status = "configured"
                else:
                    github_status = "not_configured"
            except Exception as e:
                github_status = "error"
                github_error = str(e)[:100]
            
            # Overall health determination
            overall_status = "healthy"
            if jira_status == "error" or github_status == "error":
                overall_status = "unhealthy"
            elif jira_status == "no_data" or github_status == "not_configured":
                overall_status = "degraded"
            
            health_data = {
                "status": overall_status,
                "timestamp": current_time.isoformat(),
                "uptime_seconds": int(uptime_seconds),
                "uptime_human": self._format_uptime(uptime_seconds),
                "services": {
                    "jira": {
                        "status": jira_status,
                        "cached_issues": len(jira_issues) if 'jira_issues' in locals() else 0,
                        "last_sync": self.metrics.get("last_jira_sync"),
                        "error": jira_error
                    },
                    "github": {
                        "status": github_status,
                        "configured_repo": f"{self.config.github.owner}/{self.config.github.repo}",
                        "error": github_error
                    }
                },
                "version": "1.0.0"
            }
            
            # Set appropriate HTTP status code
            status_code = 200 if overall_status == "healthy" else 503
            return JSONResponse(content=health_data, status_code=status_code)
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get server metrics and statistics."""
            current_time = datetime.now(timezone.utc)
            uptime_seconds = time.time() - self.start_time
            
            return {
                "timestamp": current_time.isoformat(),
                "uptime_seconds": int(uptime_seconds),
                "uptime_human": self._format_uptime(uptime_seconds),
                "metrics": self.metrics.copy(),
                "jira": {
                    "cached_issues": len(self.jira_client.get_all_issues()),
                    "project_key": self.config.jira.project_key,
                },
                "github": {
                    "repo": f"{self.config.github.owner}/{self.config.github.repo}",
                }
            }
        
        @self.app.get("/status", response_class=HTMLResponse)
        async def status_dashboard():
            """Simple status dashboard page."""
            current_time = datetime.now(timezone.utc)
            uptime_seconds = time.time() - self.start_time
            
            # Get health status
            jira_issues = self.jira_client.get_all_issues()
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Jira-GitHub MCP Server Status</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                    .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .status-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                    .status-card {{ padding: 20px; border-radius: 6px; border-left: 4px solid #28a745; }}
                    .status-card.degraded {{ border-left-color: #ffc107; }}
                    .status-card.error {{ border-left-color: #dc3545; }}
                    .metric {{ display: flex; justify-content: space-between; margin: 10px 0; }}
                    .metric-label {{ font-weight: 500; }}
                    .metric-value {{ color: #666; }}
                    .timestamp {{ text-align: center; color: #666; font-size: 0.9em; margin-top: 20px; }}
                    h1 {{ color: #333; }}
                    h3 {{ margin-top: 0; color: #555; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔗 Jira-GitHub MCP Server</h1>
                        <p>Real-time status and metrics</p>
                    </div>
                    
                    <div class="status-grid">
                        <div class="status-card">
                            <h3>📊 Server Metrics</h3>
                            <div class="metric">
                                <span class="metric-label">Uptime:</span>
                                <span class="metric-value">{self._format_uptime(uptime_seconds)}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Webhooks Received:</span>
                                <span class="metric-value">{self.metrics['webhooks_received']}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Issues Created:</span>
                                <span class="metric-value">{self.metrics['jira_issues_created']}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Similar Found:</span>
                                <span class="metric-value">{self.metrics['similar_issues_found']}</span>
                            </div>
                        </div>
                        
                        <div class="status-card">
                            <h3>🎯 Jira Integration</h3>
                            <div class="metric">
                                <span class="metric-label">Project:</span>
                                <span class="metric-value">{self.config.jira.project_key}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Cached Issues:</span>
                                <span class="metric-value">{len(jira_issues)}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Host:</span>
                                <span class="metric-value">{self.config.jira.host}</span>
                            </div>
                        </div>
                        
                        <div class="status-card">
                            <h3>🐙 GitHub Integration</h3>
                            <div class="metric">
                                <span class="metric-label">Repository:</span>
                                <span class="metric-value">{self.config.github.owner}/{self.config.github.repo}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Webhook Port:</span>
                                <span class="metric-value">{self.config.server.port}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="timestamp">
                        Last updated: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}
                        <br>
                        <a href="/health">JSON Health Check</a> | 
                        <a href="/metrics">Raw Metrics</a>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)

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
                
                # Update metrics
                self.metrics["webhooks_received"] += 1
                self.metrics["last_webhook_time"] = datetime.now(timezone.utc).isoformat()
                
                logger.info(f"Received GitHub webhook: {event_type} (total: {self.metrics['webhooks_received']})")

                # Process event in background
                background_tasks.add_task(
                    self._handle_webhook_event, event_type, payload
                )

                return {"success": True}

            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON payload")
            except Exception as error:
                self.metrics["errors_encountered"] += 1
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
        self, pr_number: int, comment: str, threshold: float = 0.44
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

            # Check if PR already has a JIRA issue created
            existing_jira_key = await self.github_client.has_existing_jira_issue(pr_number)
            if existing_jira_key:
                logger.info(f"PR #{pr_number} already has JIRA issue {existing_jira_key}")
                
                # Add comment to PR about existing issue
                await self.github_client.add_comment(
                    pr_number,
                    f"ℹ️ **JIRA issue already exists for this PR:**\n\n"
                    f"[{existing_jira_key}]({self.config.jira.host}/browse/{existing_jira_key})\n\n"
                    f"No need to create a duplicate issue. Please use the existing one above."
                )
                
                # Update metrics
                self.metrics["duplicates_prevented"] += 1
                
                return ProcessingResult(
                    action="duplicate_prevented",
                    reason=f"PR already has JIRA issue {existing_jira_key}"
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
                self.metrics["last_jira_sync"] = datetime.now(timezone.utc).isoformat()

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

                # Update metrics
                self.metrics["similar_issues_found"] += 1

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

            # Update metrics
            self.metrics["jira_issues_created"] += 1

            logger.info(f"Created Jira issue: {new_issue.key}")

            return ProcessingResult(action="created", issue=new_issue)

        except Exception as error:
            # Update metrics
            self.metrics["errors_encountered"] += 1
            
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
            self.metrics["last_jira_sync"] = datetime.now(timezone.utc).isoformat()
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