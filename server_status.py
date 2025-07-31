#!/usr/bin/env python3
"""Server status and management script."""

import subprocess
import sys
import time


def check_server_status():
    """Check if the MCP server is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "src.main mcp"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            return [pid for pid in pids if pid]
        return []
    except Exception as e:
        print(f"Error checking server status: {e}")
        return []


def stop_server():
    """Stop the MCP server."""
    pids = check_server_status()
    if not pids:
        print("❌ No MCP server process found")
        return False
    
    for pid in pids:
        try:
            subprocess.run(["kill", pid])
            print(f"✅ Stopped server process {pid}")
        except Exception as e:
            print(f"❌ Error stopping process {pid}: {e}")
    
    return True


def start_server():
    """Start the MCP server."""
    if check_server_status():
        print("⚠️  MCP server is already running")
        return False
    
    try:
        subprocess.Popen(
            ["python", "-m", "src.main", "mcp"],
            stdout=open("mcp_server.log", "a"),
            stderr=subprocess.STDOUT
        )
        print("🚀 MCP server started")
        time.sleep(2)  # Give it time to start
        return True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False


def show_logs(lines=20):
    """Show recent server logs."""
    try:
        result = subprocess.run(
            ["tail", f"-{lines}", "mcp_server.log"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("📝 Recent server logs:")
            print("-" * 50)
            print(result.stdout)
        else:
            print("❌ No logs found or error reading logs")
    except Exception as e:
        print(f"❌ Error reading logs: {e}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python server_status.py status    # Check server status")
        print("  python server_status.py start     # Start the server")
        print("  python server_status.py stop      # Stop the server")
        print("  python server_status.py restart   # Restart the server")
        print("  python server_status.py logs      # Show recent logs")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        pids = check_server_status()
        if pids:
            print(f"✅ MCP server is running (PIDs: {', '.join(pids)})")
        else:
            print("❌ MCP server is not running")
    
    elif command == "start":
        start_server()
    
    elif command == "stop":
        stop_server()
    
    elif command == "restart":
        print("🔄 Restarting MCP server...")
        stop_server()
        time.sleep(2)
        start_server()
    
    elif command == "logs":
        lines = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        show_logs(lines)
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()