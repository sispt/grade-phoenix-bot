#!/usr/bin/env python3
"""
Script to run scheduled grade check for all users (for use with cron or as a loop)
"""
import asyncio
import os
from bot.core import TelegramBot
from utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("cron_grade_check")

async def main():
    logger.info("🚦 [CRON] Starting scheduled grade check loop...")
    bot = TelegramBot()
    await bot.start()  # Initializes app, handlers, etc.
    interval = int(os.getenv("GRADE_CHECK_INTERVAL", 10)) * 60
    try:
        while True:
            count = await bot._notify_all_users_grades()
            logger.info(f"✅ [CRON] Grade check complete. Notified {count} users.")
            await asyncio.sleep(interval)
    finally:
        await bot.stop()

if __name__ == "__main__":
    # Set env var so bot doesn't start background tasks
    os.environ["RUN_GRADE_CHECK"] = "1"
    asyncio.run(main())
