#!/usr/bin/env python3
"""
Manual test for scheduled tasks - simulates bot environment
"""

import asyncio
import os
import sys
import time
from datetime import datetime, timedelta, timezone
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import bot components
from config import CONFIG
from storage.models import DatabaseManager
from storage.user_storage_v2 import UserStorageV2
from storage.grade_storage_v2 import GradeStorageV2
from utils.analytics import GradeAnalytics
from university.api_client_v2 import UniversityAPIV2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockBot:
    """Mock bot class to test scheduled tasks"""
    
    def __init__(self):
        self.running = True
        # Use SQLite for testing
        database_url = "sqlite:///data/test_bot.db"
        self.user_storage = UserStorageV2(database_url)
        self.grade_storage = GradeStorageV2(database_url)
        self.grade_analytics = GradeAnalytics(self.user_storage)
        self.university_api = UniversityAPIV2()
        
    async def send_quote_to_all_users(self, message):
        """Mock send quote to users"""
        users = self.user_storage.get_all_users()
        sent = 0
        for user in users:
            try:
                logger.info(f"📤 Would send quote to user {user.get('username', 'Unknown')}: {message[:50]}...")
                sent += 1
            except Exception as e:
                logger.error(f"❌ Failed to send quote to user: {e}")
        return sent
    
    async def scheduled_daily_quote_broadcast(self):
        """Send daily quote to all users at scheduled time"""
        import pytz
        from datetime import datetime, time, timedelta
        tz = pytz.timezone('Asia/Riyadh')
        
        def get_scheduled_time():
            time_str = os.getenv("QUOTE_SCHEDULE", "14:00")
            try:
                hour, minute = map(int, time_str.strip().split(":"))
                if 0 <= hour < 24 and 0 <= minute < 60:
                    return hour, minute
            except Exception:
                pass
            return 14, 0  # default time
        
        target_hour, target_minute = get_scheduled_time()
        logger.info(f"🕑 Daily quote scheduler started (UTC+3) at {target_hour:02d}:{target_minute:02d}")
        
        while self.running:
            now = datetime.now(tz)
            next_run = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)
            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"Next daily quote broadcast in {wait_seconds/60:.1f} minutes")
            
            # For testing, use a shorter wait time
            test_wait = min(wait_seconds, 10)  # Max 10 seconds for testing
            logger.info(f"⏳ Waiting {test_wait} seconds for testing...")
            await asyncio.sleep(test_wait)
            
            if not self.running:
                break
                
            # Fetch and send the quote
            quote = await self.grade_analytics.get_daily_quote()
            if quote:
                message = await self.grade_analytics.format_quote_dual_language(quote)
            else:
                message = "💬 رسالة اليوم:\n\nلم تتوفر رسالة اليوم حالياً."
            
            count = await self.send_quote_to_all_users(message)
            logger.info(f"✅ تم إرسال رسالة اليوم إلى {count} مستخدم.")
            
            # For testing, only run once
            break
    
    async def _grade_checking_loop(self):
        """Grade checking loop"""
        await asyncio.sleep(2)  # Wait a bit before starting grade check
        while self.running:
            try:
                logger.info("🔔 Running scheduled grade check for all users...")
                await self._notify_all_users_grades()
            except Exception as e:
                logger.error(f"❌ Error in scheduled grade check: {e}", exc_info=True)
            
            interval = CONFIG.get('GRADE_CHECK_INTERVAL', 10) * 60
            # For testing, use shorter interval
            test_interval = 5  # 5 seconds for testing
            logger.info(f"⏳ Waiting {test_interval} seconds before next grade check...")
            await asyncio.sleep(test_interval)
            
            # For testing, only run once
            break
    
    async def _notify_all_users_grades(self):
        """Notify all users about grade changes"""
        users = self.user_storage.get_all_users()
        logger.info(f"🔍 Force grade check: Found {len(users)} users in database")
        
        if not users:
            logger.warning("⚠️ No users found in database for grade check")
            return 0
            
        logger.info("✅ Grade check completed (mock - no actual API calls)")
        return len(users)

async def test_scheduled_tasks():
    """Test the scheduled tasks"""
    print("🚀 Testing Scheduled Tasks with Mock Bot...")
    print("=" * 50)
    
    # Create mock bot
    bot = MockBot()
    
    # Start both scheduled tasks
    grade_task = asyncio.create_task(bot._grade_checking_loop())
    quote_task = asyncio.create_task(bot.scheduled_daily_quote_broadcast())
    
    # Wait for both to complete
    await asyncio.gather(grade_task, quote_task)
    
    print("\n✅ All scheduled task tests completed!")
    
    # Stop the bot
    bot.running = False

if __name__ == "__main__":
    # Set test environment
    os.environ["QUOTE_SCHEDULE"] = "14:00"
    os.environ["GRADE_CHECK_INTERVAL"] = "15"
    
    asyncio.run(test_scheduled_tasks()) 