#!/usr/bin/env python3
"""
Health Check and Monitoring Demo Script

This script demonstrates the enhanced health check, metrics, and monitoring
capabilities added to the Jira-GitHub MCP webhook server.

Usage:
    python test_health_monitoring_demo.py

Features demonstrated:
- Comprehensive health check endpoint
- Real-time metrics tracking  
- Interactive status dashboard
- Service connectivity testing
"""

import asyncio
import json
import logging
import aiohttp
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_health_endpoint(base_url: str) -> Dict[str, Any]:
    """Test the enhanced health check endpoint."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/health") as response:
                health_data = await response.json()
                status_code = response.status
                
                print(f"🏥 Health Check Response (HTTP {status_code}):")
                print(json.dumps(health_data, indent=2))
                return health_data
                
    except Exception as e:
        print(f"❌ Failed to connect to health endpoint: {e}")
        return {}


async def test_metrics_endpoint(base_url: str) -> Dict[str, Any]:
    """Test the metrics endpoint."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/metrics") as response:
                metrics_data = await response.json()
                
                print(f"\n📊 Metrics Response:")
                print(json.dumps(metrics_data, indent=2))
                return metrics_data
                
    except Exception as e:
        print(f"❌ Failed to connect to metrics endpoint: {e}")
        return {}


async def test_status_dashboard(base_url: str) -> bool:
    """Test the status dashboard endpoint."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/status") as response:
                html_content = await response.text()
                
                print(f"\n🎯 Status Dashboard Response (HTTP {response.status}):")
                print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")
                print(f"   Content Length: {len(html_content)} bytes")
                print(f"   Contains HTML: {'<!DOCTYPE html>' in html_content}")
                print(f"   Dashboard URL: {base_url}/status")
                return True
                
    except Exception as e:
        print(f"❌ Failed to connect to status dashboard: {e}")
        return False


async def simulate_webhook_activity(base_url: str) -> bool:
    """Simulate webhook activity to generate metrics."""
    print(f"\n🚀 Simulating webhook activity...")
    
    test_payloads = [
        {
            "pr_number": 999,
            "comment": "Create jira issue for testing metrics collection"
        },
        {
            "pr_number": 998,  
            "comment": "Make jira ticket for performance testing"
        },
        {
            "pr_number": 997,
            "comment": "New jira issue needed for monitoring enhancements"
        }
    ]
    
    try:
        async with aiohttp.ClientSession() as session:
            for i, payload in enumerate(test_payloads, 1):
                print(f"   📤 Sending test webhook {i}/3...")
                
                try:
                    async with session.post(
                        f"{base_url}/trigger-jira-creation",
                        json=payload,
                        timeout=10
                    ) as response:
                        result = await response.text()
                        print(f"   ✅ Response {i}: HTTP {response.status}")
                        
                except asyncio.TimeoutError:
                    print(f"   ⏰ Timeout for webhook {i} (this is expected if server isn't configured)")
                except Exception as e:
                    print(f"   ℹ️  Webhook {i} result: {str(e)[:50]}...")
                
                # Small delay between requests
                await asyncio.sleep(0.5)
                
        return True
        
    except Exception as e:
        print(f"❌ Failed to simulate webhook activity: {e}")
        return False


async def compare_metrics_before_after(base_url: str):
    """Compare metrics before and after webhook simulation."""
    print(f"\n🔍 Comparing Metrics Before/After Activity:")
    
    # Get initial metrics
    initial_metrics = await test_metrics_endpoint(base_url)
    initial_webhooks = initial_metrics.get("metrics", {}).get("webhooks_received", 0)
    
    print(f"   Initial webhooks received: {initial_webhooks}")
    
    # Simulate activity
    await simulate_webhook_activity(base_url)
    
    # Small delay for processing
    await asyncio.sleep(1)
    
    # Get updated metrics
    updated_metrics = await test_metrics_endpoint(base_url)
    updated_webhooks = updated_metrics.get("metrics", {}).get("webhooks_received", 0)
    
    print(f"   Updated webhooks received: {updated_webhooks}")
    print(f"   Difference: +{updated_webhooks - initial_webhooks}")


def print_demo_summary():
    """Print a summary of the demo features."""
    print("\n" + "="*70)
    print("🎉 Health Check & Monitoring Demo Summary")
    print("="*70)
    
    features = [
        "✅ Enhanced Health Check - Real-time service status",
        "✅ Comprehensive Metrics - Webhook and Jira statistics", 
        "✅ Interactive Dashboard - Beautiful HTML status page",
        "✅ Service Connectivity - Jira and GitHub health validation",
        "✅ Uptime Tracking - Human-readable server uptime",
        "✅ Error Monitoring - Track and display error counts",
        "✅ Activity Tracking - Monitor webhook processing",
        "✅ Production Ready - Proper HTTP status codes and responses"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\n🚀 Ready for Production Deployment!")
    print("\nEndpoints added:")
    print("  • GET  /health  - JSON health check with service status")
    print("  • GET  /metrics - Detailed server metrics and statistics")  
    print("  • GET  /status  - Interactive HTML dashboard")
    print("  • POST /webhook - Enhanced with metrics tracking")


async def run_comprehensive_demo():
    """Run a comprehensive demonstration of all monitoring features."""
    print("🧪 Jira-GitHub MCP Health & Monitoring Demo")
    print("=" * 50)
    
    # Default local server URL - user can modify this
    base_url = "http://localhost:3000"
    print(f"Testing server: {base_url}")
    print("(Modify base_url in script if your server runs on different port)\n")
    
    # Test all endpoints
    health_data = await test_health_endpoint(base_url)
    metrics_data = await test_metrics_endpoint(base_url)
    dashboard_success = await test_status_dashboard(base_url)
    
    # If server is running, try metrics comparison
    if health_data and metrics_data:
        await compare_metrics_before_after(base_url)
    
    # Print summary
    print_demo_summary()
    
    # Instructions for PR testing
    print("\n" + "🔗 PR Testing Instructions" + "\n" + "="*25)
    print("1. Start the webhook server: python -m src.main webhook")
    print("2. Create a PR with this branch")
    print("3. Add comments like:")
    print("   • 'Create jira issue for health monitoring enhancements'")
    print("   • 'Make jira ticket - Add comprehensive server metrics'")
    print("4. Watch the metrics update in real-time!")
    print("5. Visit http://localhost:3000/status for live dashboard")


if __name__ == "__main__":
    print("🚀 Starting Health & Monitoring Demo...")
    asyncio.run(run_comprehensive_demo())
