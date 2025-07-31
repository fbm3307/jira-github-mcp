#!/usr/bin/env python3
"""Manual authentication test script for JIRA connection.

This script allows you to manually test JIRA authentication with both
basic and bearer authentication methods.

Usage:
    python test_auth_manual.py
    
Make sure to set your environment variables first:
    export JIRA_HOST="https://your-jira-instance.atlassian.net"
    export JIRA_USERNAME="your-email@example.com"
    export JIRA_API_TOKEN="your-api-token"
    export JIRA_PROJECT_KEY="YOUR_PROJECT"
    export JIRA_AUTH_METHOD="basic"  # or "bearer"
"""

import asyncio
import logging
import sys
from src.config import load_config, validate_config
from src.jira_client import JiraClient
from src.auth import create_authenticator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_authenticator_creation():
    """Test the authenticator creation separately."""
    logger.info("🔧 Testing authenticator creation...")
    
    try:
        config = load_config()
        
        # Test basic auth
        logger.info("Testing basic authenticator...")
        basic_auth = create_authenticator(
            username=config.jira.username,
            api_token=config.jira.api_token,
            auth_method="basic"
        )
        headers = basic_auth.get_headers()
        logger.info(f"✅ Basic auth headers: {list(headers.keys())}")
        
        # Test bearer auth
        logger.info("Testing bearer authenticator...")
        bearer_auth = create_authenticator(
            username=config.jira.username,
            api_token=config.jira.api_token,
            auth_method="bearer"
        )
        headers = bearer_auth.get_headers()
        logger.info(f"✅ Bearer auth headers: {list(headers.keys())}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Authenticator creation failed: {e}")
        return False


async def test_jira_connection(auth_method):
    """Test JIRA connection with specified auth method."""
    logger.info(f"🌐 Testing JIRA connection with {auth_method} authentication...")
    
    try:
        # Load config but override auth method
        config = load_config()
        config.jira.auth_method = auth_method
        validate_config(config)
        
        logger.info(f"Connecting to: {config.jira.host}")
        logger.info(f"Project: {config.jira.project_key}")
        logger.info(f"Auth method: {auth_method}")
        
        # Create client
        client = JiraClient(config)
        
        # Test basic connection by syncing issues
        logger.info("Syncing issues...")
        await client.sync_issues()
        
        logger.info(f"✅ Successfully synced {len(client.issues)} issues")
        
        # Test getting a specific issue if any exist
        if client.issues:
            first_issue = client.issues[0]
            logger.info(f"First issue: {first_issue.key} - {first_issue.summary}")
            
            # Test getting issue details
            issue_details = await client.get_issue(first_issue.key)
            if issue_details:
                logger.info(f"✅ Successfully retrieved issue details for {first_issue.key}")
            else:
                logger.warning(f"⚠️ Could not retrieve issue details for {first_issue.key}")
        
        # Test getting boards
        try:
            boards = await client.get_boards()
            logger.info(f"✅ Successfully retrieved {len(boards)} boards")
        except Exception as e:
            logger.warning(f"⚠️ Could not retrieve boards: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ JIRA connection failed with {auth_method} auth: {e}")
        return False


async def run_comprehensive_test():
    """Run comprehensive authentication tests."""
    logger.info("🚀 Starting comprehensive JIRA authentication test...")
    
    # Test authenticator creation
    if not test_authenticator_creation():
        logger.error("❌ Authenticator creation test failed")
        return False
    
    logger.info("")
    
    # Test both authentication methods
    methods_to_test = ["basic", "bearer"]
    results = {}
    
    for method in methods_to_test:
        logger.info(f"{'='*50}")
        success = await test_jira_connection(method)
        results[method] = success
        logger.info("")
    
    # Summary
    logger.info("📊 Test Summary:")
    logger.info(f"{'='*50}")
    
    all_passed = True
    for method, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{method.capitalize()} authentication: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        logger.info("🎉 All authentication tests passed!")
    else:
        logger.error("💥 Some authentication tests failed!")
    
    return all_passed


def check_environment():
    """Check if required environment variables are set."""
    logger.info("🔍 Checking environment variables...")
    
    try:
        config = load_config()
        validate_config(config)
        logger.info("✅ All required environment variables are set")
        logger.info(f"JIRA Host: {config.jira.host}")
        logger.info(f"JIRA Username: {config.jira.username}")
        logger.info(f"JIRA Project: {config.jira.project_key}")
        logger.info(f"Auth Method: {config.jira.auth_method}")
        return True
    except Exception as e:
        logger.error(f"❌ Environment check failed: {e}")
        logger.error("Please ensure all required environment variables are set:")
        logger.error("- JIRA_HOST")
        logger.error("- JIRA_USERNAME") 
        logger.error("- JIRA_API_TOKEN")
        logger.error("- JIRA_PROJECT_KEY")
        logger.error("- JIRA_AUTH_METHOD (optional, defaults to 'basic')")
        return False


async def main():
    """Main test function."""
    logger.info("🧪 JIRA Authentication Test Suite")
    logger.info("="*50)
    
    # Check environment first
    if not check_environment():
        sys.exit(1)
    
    logger.info("")
    
    # Run comprehensive tests
    success = await run_comprehensive_test()
    
    if success:
        logger.info("\n🎊 All tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n💀 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())