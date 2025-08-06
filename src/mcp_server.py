"""MCP server implementation for Jira-GitHub integration."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

# Official MCP SDK implementation
import sys
from dataclasses import asdict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
)

from .config import get_config
from .jira_client import JiraClient
from .github_client import GitHubClient
from .types import Config, CreateJiraIssueRequest

logger = logging.getLogger(__name__)


# Initialize the MCP server
app = Server("jira-github-mcp")

# Global clients - will be initialized when server starts
config: Optional[Config] = None
jira_client: Optional[JiraClient] = None
github_client: Optional[GitHubClient] = None


@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="sync_jira_issues",
            description="Sync all Jira issues from the configured project",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_jira_issues",
            description="Get all cached Jira issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status (optional)"},
                    "assignee": {"type": "string", "description": "Filter by assignee (optional)"},
                },
            },
        ),
        Tool(
            name="get_jira_boards",
            description="Get all Jira boards for the project",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="search_similar_issues",
            description="Find similar Jira issues based on text similarity",
            inputSchema={
                "type": "object",
                "properties": {
                    "searchText": {"type": "string", "description": "Text to search for similar issues"},
                    "threshold": {"type": "number", "description": "Similarity threshold (0.0 to 1.0, default: 0.6)"},
                },
                "required": ["searchText"],
            },
        ),
        Tool(
            name="create_jira_issue",
            description="Create a new Jira issue",
            inputSchema={
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
        ),
        Tool(
            name="get_github_pull_requests",
            description="Get GitHub pull requests",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "PR state filter", "enum": ["open", "closed", "all"]},
                },
            },
        ),
        Tool(
            name="get_pull_request_comments",
            description="Get comments for a specific pull request",
            inputSchema={
                "type": "object",
                "properties": {
                    "number": {"type": "number", "description": "Pull request number"},
                },
                "required": ["number"],
            },
        ),
        Tool(
            name="process_pr_comment_for_jira",
            description="Process a PR comment to potentially create a Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "prNumber": {"type": "number", "description": "Pull request number"},
                    "comment": {"type": "string", "description": "Comment text"},
                    "threshold": {"type": "number", "description": "Similarity threshold (default: 0.7)"},
                },
                "required": ["prNumber", "comment"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls."""
    global jira_client, github_client, config
    
    if not jira_client or not github_client or not config:
        raise RuntimeError("Clients not initialized")
    
    try:
        if name == "sync_jira_issues":
            return await _sync_jira_issues(arguments)
        elif name == "get_jira_issues":
            return await _get_jira_issues(arguments)
        elif name == "get_jira_boards":
            return await _get_jira_boards(arguments)
        elif name == "search_similar_issues":
            return await _search_similar_issues(arguments)
        elif name == "create_jira_issue":
            return await _create_jira_issue(arguments)
        elif name == "get_github_pull_requests":
            return await _get_github_pull_requests(arguments)
        elif name == "get_pull_request_comments":
            return await _get_pull_request_comments(arguments)
        elif name == "process_pr_comment_for_jira":
            return await _process_pr_comment_for_jira(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# Tool implementation functions
async def _sync_jira_issues(args: dict) -> List[TextContent]:
    """Sync Jira issues."""
    await jira_client.sync_issues()
    count = len(jira_client.get_all_issues())
    return [TextContent(type="text", text=f"Successfully synced {count} Jira issues")]


async def _get_jira_issues(args: dict) -> List[TextContent]:
    """Get Jira issues with optional filtering."""
    issues = jira_client.get_all_issues()
    
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

    return [TextContent(type="text", text=json.dumps(issues_data, indent=2))]


async def _get_jira_boards(args: dict) -> List[TextContent]:
    """Get Jira boards."""
    boards = await jira_client.get_boards()
    boards_data = [
        {
            "id": board.id,
            "name": board.name,
            "type": board.type,
            "projectKey": board.project_key,
        }
        for board in boards
    ]
    return [TextContent(type="text", text=json.dumps(boards_data, indent=2))]


async def _search_similar_issues(args: dict) -> List[TextContent]:
    """Search for similar issues."""
    search_text = args["searchText"]
    threshold = args.get("threshold", 0.6)
    similar_issues = jira_client.find_similar_issues(search_text, threshold)
    
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

    return [TextContent(type="text", text=json.dumps(results_data, indent=2))]


async def _create_jira_issue(args: dict) -> List[TextContent]:
    """Create a new Jira issue."""
    request = CreateJiraIssueRequest(
        summary=args["summary"],
        description=args.get("description"),
        issue_type=args["issueType"],
        project_key=config.jira.project_key,
        labels=args.get("labels", []),
        assignee=args.get("assignee"),
        priority=args.get("priority"),
    )
    
    new_issue = await jira_client.create_issue(request)
    return [TextContent(type="text", text=f"Created Jira issue: {new_issue.key} - {new_issue.summary}")]


async def _get_github_pull_requests(args: dict) -> List[TextContent]:
    """Get GitHub pull requests."""
    state = args.get("state", "all")
    prs = await github_client.get_all_pull_requests(state)
    
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

    return [TextContent(type="text", text=json.dumps(prs_data, indent=2))]


async def _get_pull_request_comments(args: dict) -> List[TextContent]:
    """Get PR comments."""
    number = args["number"]
    comments = await github_client.get_pull_request_comments(number)
    
    comments_data = [
        {
            "id": comment.id,
            "body": comment.body,
            "user": comment.user.login if comment.user else None,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
        }
        for comment in comments
    ]

    return [TextContent(type="text", text=json.dumps(comments_data, indent=2))]


async def _process_pr_comment_for_jira(args: dict) -> List[TextContent]:
    """Process a PR comment for Jira creation."""
    pr_number = args["prNumber"]
    comment = args["comment"]
    threshold = args.get("threshold", 0.44)
    
    result = await _process_pr_comment_for_jira_impl(pr_number, comment, threshold)
    return [TextContent(type="text", text=result)]

async def _process_pr_comment_for_jira_impl(pr_number: int, comment: str, threshold: float = 0.44) -> str:
    """Implementation of PR comment processing."""
    global jira_client, github_client, config
    
    # Check if comment is requesting Jira creation
    if not github_client.is_create_jira_comment(comment):
        return "Comment does not contain a request to create a Jira issue"

    # Get PR details
    pr = await github_client.get_pull_request(pr_number)
    if not pr:
        raise Exception(f"Pull request #{pr_number} not found")

    # Extract Jira details from comment and PR
    jira_details = github_client.extract_jira_details(
        comment, pr.title, pr.body, pr.number
    )

    # Ensure issues are synced
    if jira_client.needs_sync():
        await jira_client.sync_issues()

    # Search for similar existing issues
    search_text = f"{jira_details['summary']} {jira_details['description']}"
    similar_issues = jira_client.find_similar_issues(search_text, threshold)

    if similar_issues:
        best_match = similar_issues[0]
        
        # Add comment to PR about existing issue
        await github_client.add_comment(
            pr_number,
            f"🔍 Found similar existing Jira issue: [{best_match.issue.key}]({config.jira.host}/browse/{best_match.issue.key}) - {best_match.issue.summary}\n\n"
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
        project_key=config.jira.project_key,
        labels=jira_details["labels"],
    )
    
    new_issue = await jira_client.create_issue(request)

    # Add comment to PR about created issue
    await github_client.add_comment(
        pr_number,
        f"✅ Created Jira issue: [{new_issue.key}]({config.jira.host}/browse/{new_issue.key}) - {new_issue.summary}"
    )

    return f"Created new Jira issue: {new_issue.key} - {new_issue.summary}"


async def run_mcp_server() -> None:
    """Run the MCP server with stdio transport."""
    global config, jira_client, github_client
    
    # Initialize configuration and clients
    config = get_config()
    jira_client = JiraClient(config)
    github_client = GitHubClient(config)
    
    # Initial sync of Jira issues
    try:
        await jira_client.sync_issues()
        logger.info("Initial Jira sync completed")
    except Exception as error:
        logger.error(f"Failed to sync Jira issues on startup: {error}")

    logger.info(f"Starting {config.server.name} MCP server")
    
    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        ) 