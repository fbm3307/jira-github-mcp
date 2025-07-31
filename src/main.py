#!/usr/bin/env python3
"""Main entry point for the Jira-GitHub MCP server."""

import asyncio
import logging
import sys
from typing import Optional

from .config import get_config
from .webhook_server import run_webhook_server
from .mcp_server import run_mcp_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.main [mcp|webhook|both]")
        sys.exit(1)

    mode = sys.argv[1].lower()
    
    try:
        # Load configuration first
        config = get_config()
        logger.info(f"Configuration loaded successfully")
        
        if mode == "mcp":
            logger.info("Starting MCP server...")
            await run_mcp_server()
        elif mode == "webhook":
            logger.info("Starting webhook server...")
            await run_webhook_server()
        elif mode == "both":
            logger.info("Starting both MCP and webhook servers...")
            # Run both servers concurrently
            await asyncio.gather(
                run_mcp_server(),
                run_webhook_server(),
            )
        else:
            logger.error(f"Invalid mode: {mode}")
            print("Usage: python -m src.main [mcp|webhook|both]")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as error:
        logger.error(f"Server startup error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 