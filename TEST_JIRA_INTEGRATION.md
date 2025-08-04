# Test Jira Integration

This is a test file to demonstrate the Jira-GitHub integration functionality.

## Testing Scenarios

### 1. Basic Jira Creation Request
Comment: `create jira issue for testing`

### 2. Detailed Jira Creation Request
```
Create Jira
Summary: Test integration between GitHub and Jira
Type: Task
Labels: testing, integration
```

### 3. Bug Report
Comment: `create jira issue - found a critical bug in the authentication flow`

## Expected Behavior

When someone comments on a PR with a request to create a Jira issue:

1. **Webhook server** receives the GitHub event
2. **Comment analysis** determines if it's a Jira creation request  
3. **Similarity search** checks against 1000+ existing Jira issues
4. **Action taken**:
   - If similar issue exists → Comments with link to existing issue
   - If no match → Creates new Jira issue and comments with link

## System Status
- ✅ Webhook Server: Running on port 3000
- ✅ MCP Server: Running in stdio mode
- ✅ ngrok Tunnel: https://a204bc4122c6.ngrok-free.app
- ✅ Jira Sync: 1000 issues cached
- ✅ GitHub Webhook: Configured and tested

---

**Ready for testing!** 🚀