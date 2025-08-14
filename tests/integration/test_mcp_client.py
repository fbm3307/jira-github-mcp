#!/usr/bin/env python3
"""Simple MCP client to test the server functionality."""

import asyncio
import json
import subprocess
import sys
from datetime import datetime


class MCPClient:
    """Simple MCP client for testing."""
    
    def __init__(self):
        self.process = None
    
    async def start_server_process(self):
        """Start the MCP server process."""
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "src.main", "mcp",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait a moment for server to initialize
        await asyncio.sleep(2)
    
    async def send_request(self, method: str, params: dict = None):
        """Send a request to the MCP server."""
        if not self.process:
            await self.start_server_process()
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        # Send request
        request_str = json.dumps(request) + "\n"
        self.process.stdin.write(request_str.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        if response_line:
            return json.loads(response_line.decode())
        return None
    
    async def list_tools(self):
        """List available tools."""
        print("🛠️  Listing available tools...")
        response = await self.send_request("tools/list")
        if response and "result" in response:
            tools = response["result"].get("tools", [])
            print(f"Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
        return response
    
    async def sync_jira_issues(self):
        """Sync JIRA issues."""
        print("🔄 Syncing JIRA issues...")
        response = await self.send_request("tools/call", {
            "name": "sync_jira_issues",
            "arguments": {}
        })
        if response and "result" in response:
            result = response["result"]
            print(f"✅ Sync completed: {result.get('content', 'Unknown result')}")
        return response
    
    async def get_jira_issues(self, limit: int = 5):
        """Get JIRA issues."""
        print(f"📋 Getting {limit} JIRA issues...")
        response = await self.send_request("tools/call", {
            "name": "get_jira_issues", 
            "arguments": {"limit": limit}
        })
        if response and "result" in response:
            content = response["result"].get("content", "")
            print(f"✅ Retrieved issues:\n{content[:500]}..." if len(content) > 500 else content)
        return response
    
    async def search_similar_issues(self, query: str):
        """Search for similar issues."""
        print(f"🔍 Searching for issues similar to: '{query}'")
        response = await self.send_request("tools/call", {
            "name": "search_similar_issues",
            "arguments": {"search_text": query, "threshold": 0.3}
        })
        if response and "result" in response:
            content = response["result"].get("content", "")
            print(f"✅ Search results:\n{content[:500]}..." if len(content) > 500 else content)
        return response
    
    async def create_test_issue(self):
        """Create a test JIRA issue."""
        print("➕ Creating a test JIRA issue...")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = await self.send_request("tools/call", {
            "name": "create_jira_issue",
            "arguments": {
                "project_key": "SANDBOX",
                "summary": f"Test issue created via MCP - {timestamp}",
                "description": "This is a test issue created through the MCP server to verify functionality.",
                "issue_type": "Task",
                "labels": ["mcp-test", "automated"]
            }
        })
        if response and "result" in response:
            content = response["result"].get("content", "")
            print(f"✅ Issue created:\n{content}")
        return response
    
    async def close(self):
        """Close the client connection."""
        if self.process:
            self.process.terminate()
            await self.process.wait()


async def main():
    """Main function to demonstrate MCP server functionality."""
    print("🚀 Starting MCP Client Demo")
    print("=" * 50)
    
    client = MCPClient()
    
    try:
        # List available tools
        await client.list_tools()
        print()
        
        # Get some JIRA issues
        await client.get_jira_issues(3)
        print()
        
        # Search for similar issues
        await client.search_similar_issues("authentication")
        print()
        
        # Create a test issue (uncomment if you want to test creation)
        # await client.create_test_issue()
        # print()
        
        print("🎉 Demo completed successfully!")
        
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Error during demo: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())