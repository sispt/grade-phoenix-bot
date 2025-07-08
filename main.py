#!/usr/bin/env python3
"""
Main entry point for the Telegram University Bot.
بوت إشعارات الدرجات الجامعية - نقطة البداية الرئيسية
"""
import asyncio
import logging
import os
import sys
import signal
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from storage.models import Base

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.core import TelegramBot
from config import CONFIG
from storage.models import Base, DatabaseManager

# Import enhanced logging system
from utils.logger import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger("main")

logger.info("🚀 Main script starting - enhanced logging system active")


class BotRunner:
    """Main bot runner (webhook only)"""

    def __init__(self):
        self.bot = TelegramBot()
        self.running = False
        self.start_time = None

    def start(self):
        """Start the bot with all features"""
        try:
            logger.info("🚀 Starting Telegram University Bot...")
            self.start_time = datetime.now()
            self.running = True

            # Create necessary directories
            self.create_directories()

            # Run database migrations first
            self.run_migrations()

            # Automatically create all tables (schema) before starting the bot
            if CONFIG.get("USE_POSTGRESQL", False):
                logger.info(
                    "🗄️ Creating database tables (if not exist) using SQLAlchemy models..."
                )
                db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
                Base.metadata.create_all(bind=db_manager.engine)
                logger.info("✅ Database tables checked/created.")

            # Start the bot (blocking)
            asyncio.run(self.bot.start())

            logger.info("✅ Bot started successfully!")
            logger.info(f"📊 Admin ID: {CONFIG['ADMIN_ID']}")
            logger.info(f"🕒 Start time: {self.start_time}")
            logger.info(
                f"🗄️ Database: {'PostgreSQL' if CONFIG.get('USE_POSTGRESQL', False) else 'File-based'}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            raise

    def run_migrations(self):
        """Run database migrations"""
        try:
            logger.info("🔄 Running database migrations...")
            # Migration script removed; nothing to run here
            logger.info("✅ Database migrations completed (no migration script)")
        except Exception as e:
            logger.error(f"❌ Migration error: {e}")
            if CONFIG.get("USE_POSTGRESQL", False):
                # If PostgreSQL is required, fail
                raise
            else:
                # If using file storage, continue
                logger.info("🔄 Continuing with file-based storage...")

    def stop(self):
        """Stop the bot gracefully"""
        logger.info("🛑 Stopping bot...")
        self.running = False

        if self.bot:
            # If bot.stop is async, run it in event loop
            try:
                import asyncio
                asyncio.run(self.bot.stop())
            except Exception as e:
                logger.error(f"❌ Error stopping bot: {e}")

        logger.info("✅ Bot stopped successfully!")

    def create_directories(self):
        """Create necessary directories"""
        directories = [
            CONFIG["DATA_DIR"],
            CONFIG.get("LOGS_DIR", "logs"),
            CONFIG.get("BACKUP_DIR", "backups"),
        ]

        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            logger.info(f"📁 Created directory: {directory}")


def check_environment():
    """Check if all required environment variables are set"""
    required_vars = ["TELEGRAM_TOKEN", "ADMIN_ID"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        logger.info("💡 Please set the following environment variables:")
        for var in missing_vars:
            logger.info(f"   export {var}=your_value")
        return False

    return True


def auto_migrate_database(database_url):
    """
    Auto-migrate the grades table to use user_id as FK to users.id.
    Adds user_id column if missing, migrates data from telegram_id, and sets up FK.
    """
    engine = create_engine(database_url)
    insp = inspect(engine)
    with engine.connect() as conn:
        # Check if 'user_id' column exists in 'grades'
        columns = [col['name'] for col in insp.get_columns('grades')]
        if 'user_id' not in columns:
            print("[MIGRATION] Adding user_id column to grades table...")
            conn.execute(text('ALTER TABLE grades ADD COLUMN user_id INTEGER'))
            # Migrate data: set user_id based on telegram_id
            print("[MIGRATION] Migrating user_id values from telegram_id...")
            conn.execute(text('UPDATE grades SET user_id = (SELECT id FROM users WHERE users.telegram_id = grades.telegram_id)'))
            # Set user_id as NOT NULL (if all rows have user_id)
            conn.execute(text('ALTER TABLE grades ALTER COLUMN user_id SET NOT NULL'))
            # Add FK constraint
            print("[MIGRATION] Adding foreign key constraint on user_id...")
            conn.execute(text('ALTER TABLE grades ADD CONSTRAINT fk_grades_user_id FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE'))
            # Optional: drop telegram_id column if no longer needed
            # conn.execute(text('ALTER TABLE grades DROP COLUMN telegram_id'))
            print("[MIGRATION] Migration complete.")
        else:
            print("[MIGRATION] user_id column already exists in grades table. No migration needed.")


def main():
    """Main function"""
    # Check environment
    if not check_environment():
        sys.exit(1)

    # Create bot runner
    runner = BotRunner()

    # Set up signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        runner.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        runner.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        runner.stop()


if __name__ == "__main__":
    print("🎓 grade-phoenix-bot v2.1.0")
    print("بوت إشعارات الدرجات الجامعية (grade-phoenix-bot)")
    print("=" * 50)

    try:
        main()
    except Exception as e:
        logger.error(f"❌ Failed to run bot: {e}")
        sys.exit(1)
