#!/usr/bin/env python3
"""
Test script to validate duplicate Jira issue detection.

This script tests the regex pattern used to detect existing Jira issues
in PR comments to ensure the duplicate detection works properly.
"""

import re


def test_jira_detection_regex():
    """Test the regex pattern for detecting existing Jira issues."""
    
    # Current pattern (fixed)
    jira_issue_pattern = r'✅.*\*\*Created Jira issue:\*\*.*?\[([A-Z]+-\d+)\]'
    
    # Sample comment formats that should be detected
    test_comments = [
        # Standard format from webhook_server.py
        """✅ **Created Jira issue:**

[SANDBOX-1382](https://issues.redhat.com/browse/SANDBOX-1382) - Add comprehensive health monitoring system

**Type:** Task
**Labels:** enhancement, githubpr, healthcheck, monitoring""",
        
        # Minimal format
        "✅ **Created Jira issue:** [PROJ-123](https://example.com/browse/PROJ-123)",
        
        # With extra text
        "✅ **Created Jira issue:**\n\n[SANDBOX-999](https://issues.redhat.com/browse/SANDBOX-999) - Test issue\n\nSome other text",
        
        # From the actual PR
        "✅ **Created Jira issue:** [SANDBOX-1383](https://issues.redhat.com/browse/SANDBOX-1383) - [GitHub PR] Add MCP integration demo script and update documentation **Type:** Task **Labels:** githubpr"
    ]
    
    # Comments that should NOT be detected
    negative_test_comments = [
        "Create jira issue",
        "Some other comment about Jira",
        "❌ Error creating Jira issue",
        "🔍 Found similar existing Jira issue: [SANDBOX-123](link) - Summary"
    ]
    
    print("🧪 Testing Jira Issue Detection Regex")
    print("=" * 50)
    
    print("\n✅ Testing POSITIVE cases (should find Jira keys):")
    for i, comment in enumerate(test_comments, 1):
        print(f"\nTest {i}:")
        print(f"Comment: {comment[:100]}{'...' if len(comment) > 100 else ''}")
        
        match = re.search(jira_issue_pattern, comment, re.DOTALL)
        if match:
            jira_key = match.group(1)
            print(f"✅ FOUND: {jira_key}")
        else:
            print("❌ NOT FOUND - REGEX FAILED!")
    
    print(f"\n❌ Testing NEGATIVE cases (should NOT find Jira keys):")
    for i, comment in enumerate(negative_test_comments, 1):
        print(f"\nTest {i}: {comment}")
        
        match = re.search(jira_issue_pattern, comment, re.DOTALL)
        if match:
            jira_key = match.group(1)
            print(f"❌ FALSE POSITIVE: Found {jira_key}")
        else:
            print("✅ CORRECTLY IGNORED")


def test_improved_regex():
    """Test an improved regex pattern that might be more robust."""
    
    print(f"\n" + "="*50)
    print("🔧 Testing IMPROVED Regex Pattern")
    print("="*50)
    
    # More robust pattern that looks for the success checkmark + created Jira issue + link pattern
    improved_pattern = r'✅.*(?:\*\*)?Created Jira issue(?:\*\*)?:.*?\[([A-Z]+-\d+)\]'
    
    # Test the same comments
    test_comment = """✅ **Created Jira issue:**

[SANDBOX-1382](https://issues.redhat.com/browse/SANDBOX-1382) - Add comprehensive health monitoring system

**Type:** Task
**Labels:** enhancement, githubpr, healthcheck, monitoring"""
    
    print(f"Testing improved pattern: {improved_pattern}")
    print(f"On comment: {test_comment[:100]}...")
    
    match = re.search(improved_pattern, test_comment, re.DOTALL)
    if match:
        jira_key = match.group(1)
        print(f"✅ IMPROVED PATTERN FOUND: {jira_key}")
    else:
        print("❌ IMPROVED PATTERN FAILED!")


if __name__ == "__main__":
    test_jira_detection_regex()
    test_improved_regex()
    
    print(f"\n" + "="*50)
    print("💡 Recommendation:")
    print("If tests show failures, update the regex pattern in:")
    print("   src/github_client.py -> has_existing_jira_issue()")
    print("=" * 50)
