"""MCP server implementation for Jira-GitHub integration."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

# Simplified MCP implementation for now - we'll implement our own MCP protocol
import sys
from dataclasses import asdict

from .config import get_config
from .jira_client import JiraClient
from .github_client import GitHubClient
from .types import Config, CreateJiraIssueRequest

logger = logging.getLogger(__name__)


class SimpleMCPServer:
    """Simplified MCP server implementation."""
    
    def __init__(self, name: str):
        self.name = name
        self.tools = []
        self.tool_handlers = {}
    
    def add_tool(self, name: str, description: str, input_schema: dict, handler):
        """Add a tool to the server."""
        self.tools.append({
            "name": name,
            "description": description,
            "inputSchema": input_schema
        })
        self.tool_handlers[name] = handler
    
    async def handle_request(self, request: dict) -> dict:
        """Handle an MCP request."""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/list":
            return {"tools": self.tools}
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name in self.tool_handlers:
                try:
                    result = await self.tool_handlers[tool_name](arguments)
                    return {"content": [{"type": "text", "text": result}]}
                except Exception as e:
                    return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}
            else:
                return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}
        else:
            return {"error": f"Unknown method: {method}"}


class JiraGitHubMCPServer:
    """MCP server for Jira-GitHub integration."""

    def __init__(self):
        """Initialize the MCP server."""
        self.config = get_config()
        self.jira_client = JiraClient(self.config)
        self.github_client = GitHubClient(self.config)
        self.server = SimpleMCPServer(self.config.server.name)
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Set up MCP tools."""

        # Tool 1: Sync Jira issues
        self.server.add_tool(
            "sync_jira_issues",
            "Sync all Jira issues from the configured project",
            {"type": "object", "properties": {}},
            self._sync_jira_issues
        )

        # Tool 2: Get Jira issues
        self.server.add_tool(
            "get_jira_issues",
            "Get all cached Jira issues",
            {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status (optional)"},
                    "assignee": {"type": "string", "description": "Filter by assignee (optional)"},
                },
            },
            self._get_jira_issues
        )

        # Tool 3: Get Jira boards
        self.server.add_tool(
            "get_jira_boards",
            "Get all Jira boards for the project",
            {"type": "object", "properties": {}},
            self._get_jira_boards
        )

        # Tool 4: Search similar issues
        self.server.add_tool(
            "search_similar_issues",
            "Find similar Jira issues based on text similarity",
            {
                "type": "object",
                "properties": {
                    "searchText": {"type": "string", "description": "Text to search for similar issues"},
                    "threshold": {"type": "number", "description": "Similarity threshold (0.0 to 1.0, default: 0.6)"},
                },
                "required": ["searchText"],
            },
            self._search_similar_issues
        )

        # Tool 5: Create Jira issue
        self.server.add_tool(
            "create_jira_issue",
            "Create a new Jira issue",
            {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Issue summary/title"},
                    "description": {"type": "string", "description": "Issue description"},
                    "issueType": {"type": "string", "description": "Issue type", "enum": ["Bug", "Task", "Story", "Epic"]},
                    "labels": {"type": "array", "items": {"type": "string"}, "description": "Issue labels"},
                    "assignee": {"type": "string", "description": "Assignee username"},
                    "priority": {"type": "string", "description": "Issue priority", "enum": ["Highest", "High", "Medium", "Low", "Lowest"]},
                },
                "required": ["summary", "issueType"],
            },
            self._create_jira_issue
        )

        # Tool 6: Get GitHub PRs
        self.server.add_tool(
            "get_github_pull_requests",
            "Get GitHub pull requests",
            {
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "PR state filter", "enum": ["open", "closed", "all"]},
                },
            },
            self._get_github_pull_requests
        )

        # Tool 7: Get PR comments
        self.server.add_tool(
            "get_pull_request_comments",
            "Get comments for a specific pull request",
            {
                "type": "object",
                "properties": {
                    "number": {"type": "number", "description": "Pull request number"},
                },
                "required": ["number"],
            },
            self._get_pull_request_comments
        )

        # Tool 8: Process PR comment for Jira
        self.server.add_tool(
            "process_pr_comment_for_jira",
            "Process a PR comment to potentially create a Jira issue",
            {
                "type": "object",
                "properties": {
                    "prNumber": {"type": "number", "description": "Pull request number"},
                    "comment": {"type": "string", "description": "Comment text"},
                    "threshold": {"type": "number", "description": "Similarity threshold (default: 0.7)"},
                },
                "required": ["prNumber", "comment"],
            },
            self._process_pr_comment_for_jira
        )

    async def _sync_jira_issues(self, args: dict) -> str:
        """Sync Jira issues."""
        await self.jira_client.sync_issues()
        count = len(self.jira_client.get_all_issues())
        return f"Successfully synced {count} Jira issues"

    async def _get_jira_issues(self, args: dict) -> str:
        """Get Jira issues with optional filtering."""
        issues = self.jira_client.get_all_issues()
        
        # Apply filters
        if args.get("status"):
            status = args["status"].lower()
            issues = [issue for issue in issues if issue.status and status in issue.status.name.lower()]

        if args.get("assignee"):
            assignee = args["assignee"].lower()
            issues = [
                issue for issue in issues
                if issue.assignee and (
                    assignee in issue.assignee.display_name.lower() or
                    assignee in issue.assignee.email_address.lower()
                )
            ]

        # Convert to serializable format
        issues_data = []
        for issue in issues:
            issues_data.append({
                "id": issue.id,
                "key": issue.key,
                "summary": issue.summary,
                "description": issue.description,
                "status": issue.status.name if issue.status else None,
                "issueType": issue.issue_type.name if issue.issue_type else None,
                "assignee": issue.assignee.display_name if issue.assignee else None,
                "labels": issue.labels,
                "created": issue.created.isoformat() if issue.created else None,
                "updated": issue.updated.isoformat() if issue.updated else None,
            })

        return json.dumps(issues_data, indent=2)

    async def _get_jira_boards(self, args: dict) -> str:
        """Get Jira boards."""
        boards = await self.jira_client.get_boards()
        boards_data = [
            {
                "id": board.id,
                "name": board.name,
                "type": board.type,
                "projectKey": board.project_key,
            }
            for board in boards
        ]
        return json.dumps(boards_data, indent=2)

    async def _search_similar_issues(self, args: dict) -> str:
        """Search for similar issues."""
        search_text = args["searchText"]
        threshold = args.get("threshold", 0.6)
        similar_issues = self.jira_client.find_similar_issues(search_text, threshold)
        
        results_data = [
            {
                "score": result.score,
                "matchedFields": result.matched_fields,
                "issue": {
                    "key": result.issue.key,
                    "summary": result.issue.summary,
                    "description": result.issue.description,
                    "status": result.issue.status.name if result.issue.status else None,
                },
            }
            for result in similar_issues
        ]

        return json.dumps(results_data, indent=2)

    async def _create_jira_issue(self, args: dict) -> str:
        """Create a new Jira issue."""
        request = CreateJiraIssueRequest(
            summary=args["summary"],
            description=args.get("description"),
            issue_type=args["issueType"],
            project_key=self.config.jira.project_key,
            labels=args.get("labels", []),
            assignee=args.get("assignee"),
            priority=args.get("priority"),
        )
        
        new_issue = await self.jira_client.create_issue(request)
        return f"Created Jira issue: {new_issue.key} - {new_issue.summary}"

    async def _get_github_pull_requests(self, args: dict) -> str:
        """Get GitHub pull requests."""
        state = args.get("state", "all")
        prs = await self.github_client.get_all_pull_requests(state)
        
        prs_data = [
            {
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "user": pr.user.login if pr.user else None,
                "created_at": pr.created_at.isoformat() if pr.created_at else None,
                "html_url": pr.html_url,
            }
            for pr in prs
        ]

        return json.dumps(prs_data, indent=2)

    async def _get_pull_request_comments(self, args: dict) -> str:
        """Get PR comments."""
        number = args["number"]
        comments = await self.github_client.get_pull_request_comments(number)
        
        comments_data = [
            {
                "id": comment.id,
                "body": comment.body,
                "user": comment.user.login if comment.user else None,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
            }
            for comment in comments
        ]

        return json.dumps(comments_data, indent=2)

    async def _process_pr_comment_for_jira(self, args: dict) -> str:
        """Process a PR comment for Jira creation."""
        pr_number = args["prNumber"]
        comment = args["comment"]
        threshold = args.get("threshold", 0.7)
        
        return await self._process_pr_comment_for_jira_impl(pr_number, comment, threshold)

    async def _process_pr_comment_for_jira_impl(self, pr_number: int, comment: str, threshold: float) -> str:
        """Implementation of PR comment processing."""
        # Check if comment is requesting Jira creation
        if not self.github_client.is_create_jira_comment(comment):
            return "Comment does not contain a request to create a Jira issue"

        # Get PR details
        pr = await self.github_client.get_pull_request(pr_number)
        if not pr:
            raise Exception(f"Pull request #{pr_number} not found")

        # Extract Jira details from comment and PR
        jira_details = self.github_client.extract_jira_details(
            comment, pr.title, pr.body, pr.number
        )

        # Ensure issues are synced
        if self.jira_client.needs_sync():
            await self.jira_client.sync_issues()

        # Search for similar existing issues
        search_text = f"{jira_details['summary']} {jira_details['description']}"
        similar_issues = self.jira_client.find_similar_issues(search_text, threshold)

        if similar_issues:
            best_match = similar_issues[0]
            
            # Add comment to PR about existing issue
            await self.github_client.add_comment(
                pr_number,
                f"🔍 Found similar existing Jira issue: [{best_match.issue.key}]({self.config.jira.host}/browse/{best_match.issue.key}) - {best_match.issue.summary}\n\n"
                f"Similarity score: {best_match.score * 100:.1f}%\n"
                f"Matched fields: {', '.join(best_match.matched_fields)}\n\n"
                f"Please check if this existing issue covers your request before creating a new one."
            )

            return f"Found similar existing issue: {best_match.issue.key} ({best_match.score * 100:.1f}% similarity). Added comment to PR with details."

        # No similar issues found, create new one
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
            f"✅ Created Jira issue: [{new_issue.key}]({self.config.jira.host}/browse/{new_issue.key}) - {new_issue.summary}"
        )

        return f"Created new Jira issue: {new_issue.key} - {new_issue.summary}"

    async def start(self) -> None:
        """Start the MCP server."""
        # Initial sync of Jira issues
        try:
            await self.jira_client.sync_issues()
            logger.info("Initial Jira sync completed")
        except Exception as error:
            logger.error(f"Failed to sync Jira issues on startup: {error}")

        logger.info(f"{self.config.server.name} MCP server started")

    def get_server(self) -> SimpleMCPServer:
        """Get the MCP server instance."""
        return self.server

    async def run_stdio(self):
        """Run the server with stdio interface."""
        logger.info("MCP Server running in stdio mode")
        logger.info("Available tools:")
        for tool in self.server.tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")
        
        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Server shutting down...")


async def run_mcp_server() -> None:
    """Run the MCP server with stdio transport."""
    server_instance = JiraGitHubMCPServer()
    await server_instance.start()
    await server_instance.run_stdio() 