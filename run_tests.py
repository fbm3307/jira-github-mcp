#!/usr/bin/env python3
"""Comprehensive test runner for Jira-GitHub MCP integration.

This script provides an easy way to run different types of tests:
- Unit tests: Test individual components without external dependencies
- Integration tests: Test MCP server and webhook interactions  
- Manual tests: Test real JIRA connections with your credentials
- Demo scripts: Run comprehensive functionality demonstrations
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and return True if successful."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(command)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, check=True, cwd=Path(__file__).parent)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {command[0]}")
        print("Please ensure the required dependencies are installed")
        return False


def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    # Check if pytest is available
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ pytest found: {result.stdout.strip()}")
            return True
        else:
            print("❌ pytest not found")
            return False
    except Exception as e:
        print(f"❌ Error checking pytest: {e}")
        return False


def run_unit_tests():
    """Run unit tests."""
    return run_command([
        sys.executable, "-m", "pytest", 
        "tests/unit/", 
        "-v", 
        "--tb=short"
    ], "Unit tests")


def run_all_tests():
    """Run all tests including unit and integration tests."""
    return run_command([
        sys.executable, "-m", "pytest", 
        "tests/unit/", "tests/integration/",
        "-v", 
        "--tb=short"
    ], "All tests")


def run_manual_test():
    """Run manual authentication test."""
    print("\n📋 Manual Test Requirements:")
    print("Before running the manual test, ensure you have set these environment variables:")
    print("- JIRA_HOST=https://your-jira-instance.atlassian.net")
    print("- JIRA_USERNAME=your-email@example.com")
    print("- JIRA_API_TOKEN=your-api-token")
    print("- JIRA_PROJECT_KEY=YOUR_PROJECT")
    print("- JIRA_AUTH_METHOD=basic  # or 'bearer'")
    print()
    
    # Check if basic environment variables are set
    required_vars = ["JIRA_HOST", "JIRA_USERNAME", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before running the manual test.")
        return False
    
    print("✅ Required environment variables are set")
    
    return run_command([
        sys.executable, "tests/manual/test_auth_manual.py"
    ], "Manual authentication test")


def main():
    """Main function."""
    print("🧪 Jira-GitHub MCP Test Runner")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run_tests.py unit     # Run unit tests only")
        print("  python run_tests.py all      # Run all automated tests") 
        print("  python run_tests.py manual   # Run manual authentication test")
        print("  python run_tests.py check    # Check dependencies")
        print("  python run_tests.py demo     # Run demo scripts")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "check":
        if check_dependencies():
            print("\n✅ All dependencies are available")
            sys.exit(0)
        else:
            print("\n❌ Some dependencies are missing")
            print("Install with: pip install pytest pytest-asyncio")
            sys.exit(1)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Dependencies check failed")
        print("Install with: pip install pytest pytest-asyncio")
        sys.exit(1)
    
    success = False
    
    if command == "unit":
        success = run_unit_tests()
    elif command == "all":
        success = run_all_tests()
    elif command == "manual":
        success = run_manual_test()
    elif command == "demo":
        success = run_command([
            sys.executable, "tests/demo/demo.py"
        ], "Demo script")
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
    
    if success:
        print(f"\n🎉 {command.capitalize()} tests completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 {command.capitalize()} tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()