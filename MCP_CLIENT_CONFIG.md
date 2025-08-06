# MCP Client Configuration Guide

## Issue: MCP Tools Settings Error

Your MCP server is running correctly! The issue is with the client configuration.

## For Cursor/VSCode with MCP Extension:

### Option 1: Settings.json Configuration
Add this to your `settings.json`:

```json
{
  "mcp.servers": {
    "jira-github-mcp": {
      "command": "python",
      "args": ["-m", "src.main", "mcp"],
      "cwd": "/home/fmehta/Projects/jira-github-mcp",
      "env": {
        "JIRA_HOST": "https://issues.redhat.com",
        "JIRA_USERNAME": "fmehta@redhat.com", 
        "JIRA_PROJECT_KEY": "SANDBOX",
        "JIRA_AUTH_METHOD": "bearer",
        "JIRA_API_TOKEN": "your-api-token",
        "GITHUB_TOKEN": "your-github-token",
        "GITHUB_WEBHOOK_SECRET": "your-webhook-secret",
        "GITHUB_OWNER": "your-github-username",
        "GITHUB_REPO": "your-repo-name"
      }
    }
  }
}
```

### Option 2: Using .env file (Recommended)
1. Create a `.env` file in the project root:

```env
# Jira Configuration
JIRA_HOST=https://issues.redhat.com
JIRA_USERNAME=fmehta@redhat.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=SANDBOX
JIRA_AUTH_METHOD=bearer

# GitHub Configuration  
GITHUB_TOKEN=your-github-personal-access-token
GITHUB_WEBHOOK_SECRET=your-webhook-secret
GITHUB_OWNER=your-github-username
GITHUB_REPO=your-repository-name

# Server Configuration
PORT=3000
MCP_SERVER_NAME=jira-github-mcp
```

2. Then configure in `settings.json`:

```json
{
  "mcp.servers": {
    "jira-github-mcp": {
      "command": "python",
      "args": ["-m", "src.main", "mcp"],
      "cwd": "/home/fmehta/Projects/jira-github-mcp"
    }
  }
}
```

## For Claude Desktop:

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or equivalent on Linux:

```json
{
  "mcpServers": {
    "jira-github-mcp": {
      "command": "python",
      "args": ["-m", "src.main", "mcp"],
      "cwd": "/home/fmehta/Projects/jira-github-mcp"
    }
  }
}
```

## Test the Configuration:

Run this test to verify your server works:

```bash
cd /home/fmehta/Projects/jira-github-mcp
python test_mcp_client.py
```

## Available Tools:

Once configured, you'll have access to these MCP tools:
- `sync_jira_issues` - Sync all Jira issues from the configured project
- `get_jira_issues` - Get all cached Jira issues  
- `get_jira_boards` - Get all Jira boards for the project
- `search_similar_issues` - Find similar Jira issues based on text similarity
- `create_jira_issue` - Create a new Jira issue
- `get_github_pull_requests` - Get GitHub pull requests
- `get_pull_request_comments` - Get comments for a specific pull request
- `process_pr_comment_for_jira` - Process a PR comment to potentially create a Jira issue

## Troubleshooting:

1. **Check environment variables**: Ensure all required variables are set
2. **Verify paths**: Make sure the `cwd` path is correct in your config
3. **Test manually**: Run `python -m src.main mcp` to verify the server starts
4. **Check logs**: Look for specific error messages in your IDE/editor