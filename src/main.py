import asyncio
import os
import logging
from src.core.config import config
from src.bot import bot

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    token = config.token
    if not token:
        logger.error("No Discord token found! Please check .env or SecretStorage.")
        # For mock purposes, maybe we don't exit? No, we should exit.
        # But wait, in sandbox I can't provide a real token.
        # So I will catch the error and log it, maybe print a message.
        return

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        await bot.close()
    except Exception as e:
        logger.error(f"Bot runtime error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
