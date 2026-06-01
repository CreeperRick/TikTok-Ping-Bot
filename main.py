#!/usr/bin/env python3
"""
Main entry point: runs both Discord bot and FastAPI web server concurrently.
"""
import asyncio
import logging
import sys
import uvicorn
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

from bot.bot import DiscordBot
from web.app import app as fastapi_app
from database.database import init_db


async def run_bot():
    """Run Discord bot."""
    bot = DiscordBot()
    await bot.start()


async def run_web():
    """Run FastAPI with Uvicorn."""
    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Initialize database and start both services concurrently."""
    logger.info("Initializing database...")
    await init_db()

    logger.info("Starting Discord bot and Web dashboard...")
    await asyncio.gather(
        run_bot(),
        run_web()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
