#!/usr/bin/env python3
"""Demo script showing how to use the Jira-GitHub MCP server."""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_mcp_tools():
    """Demonstrate MCP tools functionality."""
    from src.config import get_config
    from src.jira_client import JiraClient
    from src.github_client import GitHubClient
    from src.types import CreateJiraIssueRequest
    
    try:
        # Load configuration
        config = get_config()
        logger.info("Configuration loaded successfully")
        
        # Initialize clients
        jira_client = JiraClient(config)
        github_client = GitHubClient(config)
        logger.info("Clients initialized")
        
        # Demo 1: Sync Jira issues
        logger.info("=== Demo 1: Syncing Jira issues ===")
        await jira_client.sync_issues()
        issues = jira_client.get_all_issues()
        logger.info(f"Synced {len(issues)} issues from Jira")
        
        # Show first 3 issues
        for i, issue in enumerate(issues[:3]):
            logger.info(f"Issue {i+1}: {issue.key} - {issue.summary}")
        
        # Demo 2: Search similar issues
        logger.info("\n=== Demo 2: Searching for similar issues ===")
        search_text = "login bug"
        similar_issues = jira_client.find_similar_issues(search_text, threshold=0.3)
        logger.info(f"Found {len(similar_issues)} similar issues for '{search_text}'")
        
        for result in similar_issues[:3]:
            logger.info(f"- {result.issue.key}: {result.score:.2f} similarity - {result.issue.summary}")
        
        # Demo 3: Get GitHub PRs
        logger.info("\n=== Demo 3: Getting GitHub pull requests ===")
        prs = await github_client.get_all_pull_requests(state="open")
        logger.info(f"Found {len(prs)} open pull requests")
        
        for pr in prs[:3]:
            logger.info(f"PR #{pr.number}: {pr.title}")
        
        # Demo 4: Check Jira boards
        logger.info("\n=== Demo 4: Getting Jira boards ===")
        boards = await jira_client.get_boards()
        logger.info(f"Found {len(boards)} boards")
        
        for board in boards:
            logger.info(f"Board: {board.name} (ID: {board.id})")
        
        # Demo 5: Comment parsing
        logger.info("\n=== Demo 5: Comment parsing demo ===")
        test_comments = [
            "This looks good, let's merge it",
            "create jira issue for this bug fix",
            "Create Jira\nSummary: Fix login page styling\nType: Bug\nLabels: frontend, urgent",
        ]
        
        for comment in test_comments:
            is_jira_request = github_client.is_create_jira_comment(comment)
            logger.info(f"Comment: '{comment[:30]}...' -> Jira request: {is_jira_request}")
            
            if is_jira_request:
                details = github_client.extract_jira_details(comment, "Test PR Title", "Test PR body", 123)
                logger.info(f"  Extracted: {details['summary']} ({details['issue_type']})")
        
        logger.info("\n=== Demo completed successfully! ===")
        
    except Exception as error:
        logger.error(f"Demo failed: {error}")
        raise

async def demo_webhook_functionality():
    """Demonstrate webhook server functionality."""
    from src.webhook_server import WebhookServer
    
    logger.info("=== Webhook Server Demo ===")
    logger.info("This would start the webhook server on http://localhost:3000")
    logger.info("You can test it with:")
    logger.info("curl -X POST http://localhost:3000/trigger-jira-creation \\")
    logger.info('  -H "Content-Type: application/json" \\')
    logger.info('  -d \'{"pr_number": 123, "comment": "create jira issue"}\'')
    
    # Uncomment to actually start the webhook server
    # webhook_server = WebhookServer()
    # await webhook_server.start()

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        "JIRA_HOST", "JIRA_USERNAME", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY",
        "GITHUB_TOKEN", "GITHUB_WEBHOOK_SECRET", "GITHUB_OWNER", "GITHUB_REPO"
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error("Missing required environment variables:")
        for var in missing:
            logger.error(f"  - {var}")
        logger.error("\nPlease copy env.example to .env and fill in your credentials")
        return False
    
    logger.info("✓ All required environment variables are set")
    return True

async def main():
    """Main demo function."""
    logger.info("🚀 Jira-GitHub MCP Server Demo")
    logger.info("=" * 50)
    
    if not check_environment():
        return
    
    try:
        # Run MCP tools demo
        await demo_mcp_tools()
        
        # Show webhook demo info
        await demo_webhook_functionality()
        
        logger.info("\n" + "=" * 50)
        logger.info("Demo completed! Ready to run the full server with:")
        logger.info("python -m src.main mcp      # MCP server only")
        logger.info("python -m src.main webhook  # Webhook server only") 
        logger.info("python -m src.main both     # Both servers")
        
    except Exception as error:
        logger.error(f"Demo error: {error}")

if __name__ == "__main__":
    asyncio.run(main()) 