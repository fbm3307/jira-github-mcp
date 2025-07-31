# 🚀 MCP Server Usage Guide

Your Jira-GitHub MCP server is now running successfully! Here's how to use and manage it.

## 📊 Server Status

**✅ Server is currently running on PID: 442571**

- **Host**: Red Hat JIRA (https://issues.redhat.com)
- **Project**: SANDBOX
- **Authentication**: Bearer token (working correctly)
- **Issues synced**: 1000+ issues from JIRA

## 🛠️ Available Tools

The MCP server provides these powerful tools:

| Tool | Description |
|------|-------------|
| `sync_jira_issues` | Sync all Jira issues from the configured project |
| `get_jira_issues` | Get all cached Jira issues |
| `get_jira_boards` | Get all Jira boards for the project |
| `search_similar_issues` | Find similar Jira issues based on text similarity |
| `create_jira_issue` | Create a new Jira issue |
| `get_github_pull_requests` | Get GitHub pull requests |
| `get_pull_request_comments` | Get comments for a specific pull request |
| `process_pr_comment_for_jira` | Process a PR comment to potentially create a Jira issue |

## 🎮 Server Management

### Check Server Status
```bash
python server_status.py status
```

### View Recent Logs
```bash
python server_status.py logs       # Show last 20 lines
python server_status.py logs 50    # Show last 50 lines
```

### Stop the Server
```bash
python server_status.py stop
```

### Start the Server
```bash
python server_status.py start
```

### Restart the Server
```bash
python server_status.py restart
```

## 🧪 Testing the Server

### Run Demo Client
```bash
python test_mcp_client.py
```

This will demonstrate:
- Listing available tools
- Getting JIRA issues
- Searching for similar issues
- (Optional) Creating test issues

### Manual MCP Commands

You can also interact with the server directly using the MCP protocol:

#### List Tools
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | python -m src.main mcp
```

#### Get JIRA Issues
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_jira_issues", "arguments": {"limit": 5}}}' | python -m src.main mcp
```

#### Search Similar Issues
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "search_similar_issues", "arguments": {"search_text": "authentication", "threshold": 0.3}}}' | python -m src.main mcp
```

## 🔧 Configuration

### Environment Variables
Your current working configuration:
```bash
JIRA_HOST=https://issues.redhat.com
JIRA_USERNAME=fmehta@redhat.com
JIRA_PROJECT_KEY=SANDBOX
JIRA_AUTH_METHOD=bearer  # Required for Red Hat JIRA
```

### Authentication
- ✅ **Bearer authentication** is configured and working
- ❌ **Basic authentication** fails with Red Hat JIRA (401 Unauthorized)

## 📝 Logs

Server logs are written to `mcp_server.log` in the project directory.

### View Live Logs
```bash
tail -f mcp_server.log
```

### Search Logs
```bash
grep "ERROR" mcp_server.log     # Find errors
grep "JIRA" mcp_server.log      # Find JIRA-related entries
```

## 🚨 Troubleshooting

### Server Not Responding
1. Check if server is running: `python server_status.py status`
2. Check logs: `python server_status.py logs`
3. Restart server: `python server_status.py restart`

### Authentication Issues
- Ensure `JIRA_AUTH_METHOD=bearer` for Red Hat JIRA
- Verify your API token is valid
- Check that you have access to the SANDBOX project

### Connection Issues
- Verify network connectivity to https://issues.redhat.com
- Check firewall settings
- Ensure all required environment variables are set

## 🎯 Next Steps

1. **Integrate with your IDE**: Configure your IDE or editor to use the MCP server
2. **Create workflows**: Set up automation between GitHub PRs and JIRA issues
3. **Monitor usage**: Use the logs to monitor server activity
4. **Scale up**: Add more projects or repositories as needed

## 💡 Tips

- The server caches JIRA issues for performance - use `sync_jira_issues` to refresh
- Search uses fuzzy matching - lower thresholds find more similar issues
- All operations are logged for debugging and monitoring
- Bearer authentication is more secure and works better with modern JIRA instances

---

**🎉 Your MCP server is ready for production use!**