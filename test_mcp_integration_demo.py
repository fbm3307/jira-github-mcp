#!/usr/bin/env python3
"""
MCP Integration Demo Script

This script demonstrates how to interact with the Jira-GitHub MCP server
to test the integration between GitHub PRs and Jira ticket creation.

Usage:
    python test_mcp_integration_demo.py

Features tested:
- MCP server connection
- Jira issue synchronization
- Similar issue detection
- GitHub PR comment processing
"""

import asyncio
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mcp_integration():
    """Test the MCP integration capabilities."""
    print("🧪 Testing MCP Jira-GitHub Integration")
    print("=" * 50)
    
    # Test scenarios for Jira ticket creation
    test_scenarios = [
        {
            "name": "Bug Report from PR",
            "pr_number": 123,
            "comment": "Create jira issue - Found a bug in the authentication flow that needs investigation",
            "expected": "Should create a Bug type issue"
        },
        {
            "name": "Feature Request", 
            "pr_number": 124,
            "comment": "New jira ticket needed: Add dark mode support to the UI",
            "expected": "Should create a Task/Story type issue"
        },
        {
            "name": "Performance Issue",
            "pr_number": 125, 
            "comment": "Make jira issue for performance optimization in the search function",
            "expected": "Should detect similar existing performance issues"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n🔍 Testing: {scenario['name']}")
        print(f"   Comment: {scenario['comment']}")
        print(f"   Expected: {scenario['expected']}")
        print("   Status: Ready for testing via MCP tools")
    
    print("\n✅ Demo scenarios prepared!")
    print("\nNext steps:")
    print("1. Create PR with this branch")
    print("2. Comment on the PR with Jira creation requests")
    print("3. Watch the MCP server process the comments")
    print("4. Verify Jira tickets are created or similar issues found")


def demonstrate_comment_parsing():
    """Demonstrate different comment formats for Jira creation."""
    print("\n📝 Supported Comment Formats:")
    print("-" * 30)
    
    formats = [
        "create jira",
        "make jira issue", 
        "new jira ticket",
        "create issue for this bug",
        "create ticket",
        "jira issue needed"
    ]
    
    for fmt in formats:
        print(f"  ✓ '{fmt}'")
    
    print("\n📋 Advanced Comment Examples:")
    print("  • 'Create jira issue\\nSummary: Fix login bug\\nType: Bug\\nLabels: frontend, auth'")
    print("  • 'New jira ticket needed for performance optimization'")
    print("  • 'Make jira issue - this PR introduces a breaking change'")


if __name__ == "__main__":
    print("🚀 MCP Integration Demo")
    demonstrate_comment_parsing()
    asyncio.run(test_mcp_integration())
