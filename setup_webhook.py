#!/usr/bin/env python3
"""GitHub Webhook Setup Helper Script."""

import os
import sys
import subprocess
import requests
import json
from urllib.parse import urlparse


def check_ngrok():
    """Check if ngrok is installed."""
    try:
        result = subprocess.run(["ngrok", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ngrok is installed")
            return True
        return False
    except FileNotFoundError:
        print("❌ ngrok is not installed")
        return False


def install_ngrok_instructions():
    """Show instructions for installing ngrok."""
    print("\n📦 To install ngrok:")
    print("1. Visit https://ngrok.com/download")
    print("2. Download and install ngrok for your platform")
    print("3. Sign up for a free account at https://dashboard.ngrok.com/")
    print("4. Get your auth token and run: ngrok authtoken YOUR_AUTH_TOKEN")
    print("\nOr use the package manager:")
    print("  # On Ubuntu/Debian:")
    print("  curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null")
    print("  echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list")
    print("  sudo apt update && sudo apt install ngrok")


def start_ngrok_tunnel(port=3000):
    """Start ngrok tunnel for the webhook server."""
    try:
        print(f"🌐 Starting ngrok tunnel on port {port}...")
        # Start ngrok in the background
        process = subprocess.Popen(
            ["ngrok", "http", str(port), "--log=stdout"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give ngrok time to start
        import time
        time.sleep(3)
        
        # Get the public URL from ngrok API
        try:
            response = requests.get("http://localhost:4040/api/tunnels")
            if response.status_code == 200:
                tunnels = response.json()["tunnels"]
                if tunnels:
                    public_url = tunnels[0]["public_url"]
                    webhook_url = f"{public_url}/webhook"
                    print(f"✅ Ngrok tunnel started!")
                    print(f"🌍 Public URL: {public_url}")
                    print(f"🪝 Webhook URL: {webhook_url}")
                    return webhook_url, process
        except Exception as e:
            print(f"⚠️  Could not get ngrok URL automatically: {e}")
            print("Check ngrok dashboard at http://localhost:4040")
        
        return None, process
    except Exception as e:
        print(f"❌ Error starting ngrok: {e}")
        return None, None


def check_webhook_server():
    """Check if the webhook server is accessible."""
    try:
        response = requests.get("http://localhost:3000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Webhook server is running and accessible")
            return True
    except Exception as e:
        print(f"❌ Webhook server is not accessible: {e}")
        return False


def generate_webhook_secret():
    """Generate a secure webhook secret."""
    import secrets
    import string
    
    # Generate a 32-character random secret
    alphabet = string.ascii_letters + string.digits
    secret = ''.join(secrets.choice(alphabet) for _ in range(32))
    return secret


def create_github_webhook_instructions(webhook_url, secret):
    """Show instructions for creating GitHub webhook."""
    print("\n" + "="*60)
    print("🚀 GITHUB WEBHOOK SETUP INSTRUCTIONS")
    print("="*60)
    
    print(f"\n📋 Use these settings in your GitHub repository:")
    print(f"🌍 Payload URL: {webhook_url}")
    print(f"🔒 Secret: {secret}")
    print("📦 Content type: application/json")
    print("🎯 Events: Send me everything (or select specific events)")
    
    print(f"\n📝 Steps to create the webhook:")
    print("1. Go to your GitHub repository")
    print("2. Click Settings → Webhooks → Add webhook")
    print("3. Enter the Payload URL and Secret above")
    print("4. Select 'application/json' as content type")
    print("5. Choose events (recommended: Pull requests, Issues, Issue comments)")
    print("6. Click 'Add webhook'")
    
    print(f"\n🔧 Update your environment variables:")
    print(f"export GITHUB_WEBHOOK_SECRET='{secret}'")
    print(f"# Add this to your .env file or environment")
    
    print(f"\n🧪 Test your webhook:")
    print("1. Create a test issue or PR in your GitHub repo")
    print("2. Check the webhook deliveries in GitHub Settings → Webhooks")
    print("3. Monitor your server logs for incoming requests")


def main():
    """Main function."""
    print("🪝 GitHub Webhook Setup Helper")
    print("=" * 40)
    
    # Check if webhook server is running
    print("\n🔍 Checking webhook server status...")
    if not check_webhook_server():
        print("\n💡 Start your webhook server first:")
        print("   python -m src.main webhook")
        print("   # or")
        print("   python -m src.main both  # for both MCP and webhook servers")
        return
    
    # Check for tunnel service
    print("\n🌐 Setting up public URL for GitHub webhooks...")
    
    if check_ngrok():
        webhook_url, process = start_ngrok_tunnel()
        if webhook_url:
            secret = generate_webhook_secret()
            create_github_webhook_instructions(webhook_url, secret)
            
            print(f"\n⚠️  IMPORTANT: Keep this terminal open to maintain the tunnel!")
            print("Press Ctrl+C to stop the tunnel when done.")
            
            try:
                # Keep the script running
                process.wait()
            except KeyboardInterrupt:
                print("\n👋 Stopping ngrok tunnel...")
                process.terminate()
        else:
            print("❌ Failed to start ngrok tunnel")
            install_ngrok_instructions()
    else:
        install_ngrok_instructions()
        print("\n🌍 Alternative solutions:")
        print("- Use a cloud server (AWS, GCP, etc.)")
        print("- Use other tunnel services (localtunnel, serveo, etc.)")
        print("- Set up port forwarding on your router")
        
        # Show local information anyway
        secret = generate_webhook_secret()
        print(f"\n🔒 Generated webhook secret: {secret}")
        print("💾 Save this secret for when you have a public URL")


if __name__ == "__main__":
    main()