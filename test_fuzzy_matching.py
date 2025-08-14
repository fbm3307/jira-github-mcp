#!/usr/bin/env python3
"""
Test script to validate fuzzy matching logic for similar Jira issues.

This simulates the same issues created in PR #3 to see if they should
have been detected as similar.
"""

from fuzzywuzzy import fuzz
from dataclasses import dataclass
from typing import List, Optional
import datetime


@dataclass
class MockJiraIssue:
    key: str
    summary: str
    description: Optional[str]
    labels: List[str]


@dataclass
class MockMatchResult:
    score: float
    issue: MockJiraIssue
    matched_fields: List[str]


def find_similar_issues_test(search_text: str, issues: List[MockJiraIssue], threshold: float = 0.44) -> List[MockMatchResult]:
    """Test version of the fuzzy matching logic."""
    if not issues:
        return []

    results = []
    
    for issue in issues:
        # Create searchable text from issue
        issue_text = f"{issue.summary} {issue.description or ''} {' '.join(issue.labels)}"
        
        # Calculate similarity scores for different fields
        summary_score = fuzz.token_sort_ratio(search_text.lower(), issue.summary.lower()) / 100
        description_score = 0
        if issue.description:
            description_score = fuzz.token_sort_ratio(search_text.lower(), issue.description.lower()) / 100
        
        labels_score = 0
        if issue.labels:
            labels_text = ' '.join(issue.labels)
            labels_score = fuzz.token_sort_ratio(search_text.lower(), labels_text.lower()) / 100

        # Weighted combined score (this might be the issue!)
        combined_score = (summary_score * 0.7) + (description_score * 0.3) + (labels_score * 0.2)
        
        # Normalize to 0-1 range
        combined_score = min(combined_score, 1.0)
        
        print(f"  Issue: {issue.key}")
        print(f"    Summary score: {summary_score:.3f}")
        print(f"    Description score: {description_score:.3f}")
        print(f"    Labels score: {labels_score:.3f}")
        print(f"    Combined score: {combined_score:.3f} (threshold: {threshold})")
        
        if combined_score >= threshold:
            matched_fields = []
            if summary_score >= threshold:
                matched_fields.append('summary')
            if description_score >= threshold:
                matched_fields.append('description')
            if labels_score >= threshold:
                matched_fields.append('labels')
            
            results.append(MockMatchResult(
                score=combined_score,
                issue=issue,
                matched_fields=matched_fields
            ))

    # Sort by score descending
    results.sort(key=lambda x: x.score, reverse=True)
    return results


def test_pr3_scenario():
    """Test the exact scenario from PR #3."""
    print("🧪 Testing PR #3 Scenario - Why Similar Issues Weren't Detected")
    print("=" * 70)
    
    # Simulate the issues that were created in PR #3
    existing_issues = [
        MockJiraIssue(
            key="SANDBOX-1382",
            summary="Add comprehensive health monitoring system", 
            description="Enhanced /health endpoint with service connectivity testing\nAdded /metrics endpoint for real-time server statistics\nCreated /status interactive HTML dashboard\nImplemented metrics tracking for webhooks, issues, and errors",
            labels=["enhancement", "githubpr", "healthcheck", "monitoring"]
        )
    ]
    
    # Test search texts that should have found the existing issue
    search_scenarios = [
        {
            "name": "Second comment (should find SANDBOX-1382)",
            "search_text": "[GitHub PR] Add MCP integration demo script and update documentation Enhanced /health endpoint with service connectivity testing",
            "comment": "create jira issue"
        },
        {
            "name": "Third comment (should find SANDBOX-1382)", 
            "search_text": "[GitHub PR] Add MCP integration demo script and update documentation Enhanced /health endpoint with service connectivity testing",
            "comment": "create jira issue"
        }
    ]
    
    for scenario in search_scenarios:
        print(f"\n📝 {scenario['name']}")
        print(f"Search text: {scenario['search_text'][:100]}...")
        print(f"Comment: {scenario['comment']}")
        print()
        
        # Test with different thresholds
        for threshold in [0.44, 0.3, 0.6]:
            print(f"  Testing with threshold {threshold}:")
            similar = find_similar_issues_test(scenario['search_text'], existing_issues, threshold)
            
            if similar:
                best = similar[0]
                print(f"    ✅ FOUND: {best.issue.key} (score: {best.score:.3f})")
                print(f"    Matched fields: {best.matched_fields}")
            else:
                print(f"    ❌ NO MATCH - Would create duplicate!")
            print()


def test_improved_scoring():
    """Test with improved scoring algorithm."""
    print("\n" + "="*70)
    print("🔧 Testing Improved Scoring Algorithm")
    print("="*70)
    
    # Simple similarity test - just summary comparison for related issues
    search_text = "Add MCP integration demo script and update documentation"
    existing_summary = "Add comprehensive health monitoring system"
    
    print(f"Search: {search_text}")
    print(f"Existing: {existing_summary}")
    print()
    
    # Test different fuzzy matching algorithms
    algorithms = [
        ("ratio", fuzz.ratio),
        ("partial_ratio", fuzz.partial_ratio), 
        ("token_sort_ratio", fuzz.token_sort_ratio),
        ("token_set_ratio", fuzz.token_set_ratio)
    ]
    
    for name, algo in algorithms:
        score = algo(search_text.lower(), existing_summary.lower()) / 100
        print(f"{name:20s}: {score:.3f}")
    
    print(f"\n💡 Recommendations:")
    print(f"   - Current threshold (0.44) might be too high")
    print(f"   - token_set_ratio often works better for partial matches")
    print(f"   - Consider lowering threshold to 0.3 or using different algorithm")


if __name__ == "__main__":
    test_pr3_scenario()
    test_improved_scoring()
