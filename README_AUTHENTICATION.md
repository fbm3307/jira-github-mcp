# JIRA Authentication Testing Guide

This guide shows you how to test the new flexible JIRA authentication system that supports both Basic and Bearer authentication methods.

## 🏗️ What Was Updated

The JIRA client now supports Jayrah-style authentication with:

- **Basic Authentication**: Username + API Token (default, backward compatible)
- **Bearer Authentication**: API Token only 
- **Flexible Configuration**: Easy switching between auth methods
- **Graceful Fallback**: Invalid auth methods fall back to basic auth

## 🧪 Testing Options

### 1. Unit Tests (Automated)

Test the authentication logic without connecting to JIRA:

```bash
# Run all unit tests
python run_tests.py unit

# Check if dependencies are installed
python run_tests.py check
```

### 2. Manual Authentication Test (Real JIRA Connection)

Test with your actual JIRA instance:

#### Setup Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Required variables
export JIRA_HOST="https://your-jira-instance.atlassian.net"
export JIRA_USERNAME="your-email@example.com"  
export JIRA_API_TOKEN="your-api-token"
export JIRA_PROJECT_KEY="YOUR_PROJECT"

# Optional: Authentication method (defaults to "basic")
export JIRA_AUTH_METHOD="basic"  # or "bearer"

# GitHub variables (required but not used in auth test)
export GITHUB_TOKEN="your_github_token"
export GITHUB_WEBHOOK_SECRET="your_webhook_secret"
export GITHUB_OWNER="your_github_username"
export GITHUB_REPO="your_repo_name"
```

#### Run Manual Tests

```bash
# Test authentication with your JIRA instance
python run_tests.py manual

# Or run the test script directly
python test_auth_manual.py
```

## 🔧 Authentication Methods

### Basic Authentication (Default)
```bash
export JIRA_AUTH_METHOD="basic"
```
- Uses username + API token
- Most compatible with JIRA instances
- Recommended for most setups

### Bearer Authentication 
```bash
export JIRA_AUTH_METHOD="bearer"
```
- Uses API token only
- Modern OAuth-style authentication
- May not work with all JIRA configurations

## 📋 Manual Test Output

The manual test will:

1. ✅ **Test Authenticator Creation** - Verify auth objects work correctly
2. 🌐 **Test JIRA Connection** - Connect with both basic and bearer auth
3. 📊 **Test API Operations** - Sync issues, get boards, retrieve issue details
4. 📈 **Show Summary** - Report which authentication methods work

### Example Output:

```
🧪 JIRA Authentication Test Suite
==================================================
🔍 Checking environment variables...
✅ All required environment variables are set
JIRA Host: https://issues.redhat.com
JIRA Username: your@email.com
JIRA Project: SANDBOX
Auth Method: basic

🔧 Testing authenticator creation...
Testing basic authenticator...
✅ Basic auth headers: ['Authorization']
Testing bearer authenticator...
✅ Bearer auth headers: ['Authorization']

==================================================
🌐 Testing JIRA connection with basic authentication...
Connecting to: https://issues.redhat.com
Project: SANDBOX
Auth method: basic
Syncing issues...
✅ Successfully synced 15 issues
First issue: SANDBOX-123 - Test Issue Summary
✅ Successfully retrieved issue details for SANDBOX-123
✅ Successfully retrieved 3 boards

==================================================
🌐 Testing JIRA connection with bearer authentication...
Connecting to: https://issues.redhat.com
Project: SANDBOX  
Auth method: bearer
Syncing issues...
✅ Successfully synced 15 issues
✅ Successfully retrieved 3 boards

📊 Test Summary:
==================================================
Basic authentication: ✅ PASSED
Bearer authentication: ✅ PASSED
🎉 All authentication tests passed!
```

## 🔍 Troubleshooting

### Common Issues:

1. **"Required environment variable not set"**
   - Make sure all environment variables are properly set
   - Check for typos in variable names

2. **"Bearer authentication failed"**
   - Your JIRA instance might not support bearer auth
   - Try basic authentication instead
   - Check your API token permissions

3. **"Unauthorized" errors**
   - Verify your API token is valid and not expired
   - Ensure your username is correct for basic auth
   - Check that you have access to the specified project

4. **Connection timeouts**
   - Verify JIRA_HOST URL is correct
   - Check network connectivity to your JIRA instance

### Getting JIRA API Token:

1. Go to your JIRA profile settings
2. Navigate to "Security" → "API tokens"
3. Create a new API token
4. Copy the token to your `JIRA_API_TOKEN` environment variable

## 🚀 Next Steps

After successful authentication testing:

1. Choose your preferred authentication method
2. Update your production environment variables
3. Test with your actual workflows
4. Monitor authentication in application logs

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your JIRA instance configuration
3. Test with the Jayrah project for comparison
4. Check application logs for detailed error messages