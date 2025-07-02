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

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.core import TelegramBot
from config import CONFIG
from storage.models import Base, DatabaseManager

# Set up logging
logging.basicConfig(
    level=getattr(logging, CONFIG["LOG_LEVEL"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG["LOG_FILE"]),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("DEBUG: Main script starting - logging test")

class BotRunner:
    """Main bot runner (webhook only)"""
    
    def __init__(self):
        self.bot = TelegramBot()
        self.running = False
        self.start_time = None
        
    async def start(self):
        """Start the bot with all features"""
        try:
            logger.info("🚀 Starting Telegram University Bot...")
            self.start_time = datetime.now()
            self.running = True
            
            # Create necessary directories
            self.create_directories()
            
            # Automatically create all tables (schema) before starting the bot
            if CONFIG.get("USE_POSTGRESQL", False):
                logger.info("🗄️ Creating database tables (if not exist) using SQLAlchemy models...")
                db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
                Base.metadata.create_all(bind=db_manager.engine)
                logger.info("✅ Database tables checked/created.")
            
            # Start the bot
            await self.bot.start()
            
            logger.info("✅ Bot started successfully!")
            logger.info(f"📊 Admin ID: {CONFIG['ADMIN_ID']}")
            logger.info(f"🕒 Start time: {self.start_time}")
            logger.info(f"🗄️ Database: {'PostgreSQL' if CONFIG.get('USE_POSTGRESQL', False) else 'File-based'}")
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            raise
    
    async def run_migrations(self):
        """Run database migrations"""
        try:
            logger.info("🗄️ Running database migrations...")
            
            # Import migrations module
            from migrations import run_migrations, check_database_status
            
            # Run migrations
            if not run_migrations():
                logger.error("❌ Database migration failed")
                if CONFIG.get("USE_POSTGRESQL", False):
                    # If PostgreSQL is required, fail
                    raise Exception("Database migration failed")
                else:
                    # If using file storage, continue
                    logger.info("🔄 Continuing with file-based storage...")
                    return
            
            # Check database status
            if not check_database_status():
                logger.warning("⚠️ Database status check failed")
            
            logger.info("✅ Database migrations completed")
            
        except Exception as e:
            logger.error(f"❌ Migration error: {e}")
            if CONFIG.get("USE_POSTGRESQL", False):
                # If PostgreSQL is required, fail
                raise
            else:
                # If using file storage, continue
                logger.info("🔄 Continuing with file-based storage...")
    
    async def stop(self):
        """Stop the bot gracefully"""
        logger.info("🛑 Stopping bot...")
        self.running = False
        
        if self.bot:
            await self.bot.stop()
        
        logger.info("✅ Bot stopped successfully!")
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            CONFIG["DATA_DIR"],
            CONFIG.get("LOGS_DIR", "logs"),
            CONFIG.get("BACKUP_DIR", "backups")
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

async def main():
    """Main function"""
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Create bot runner
    runner = BotRunner()
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(runner.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await runner.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await runner.stop()

if __name__ == "__main__":
    print("🎓 Telegram University Bot v2.1.3")
    print("بوت إشعارات الدرجات الجامعية")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Failed to run bot: {e}")
        sys.exit(1) 