#!/usr/bin/env python3
"""
Test script for scheduled tasks timezone issues
"""

import asyncio
import os
import pytz
from datetime import datetime, timedelta, timezone
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_quote_scheduler():
    """Test the quote scheduler logic"""
    print("🔍 Testing Quote Scheduler Logic...")
    
    # Test timezone handling
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
    print(f"📅 Target time: {target_hour:02d}:{target_minute:02d} (UTC+3)")
    
    # Test current time calculation
    now = datetime.now(tz)
    print(f"🕒 Current time (UTC+3): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test next run calculation
    next_run = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    if now >= next_run:
        next_run += timedelta(days=1)
    
    wait_seconds = (next_run - now).total_seconds()
    print(f"⏰ Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏳ Wait time: {wait_seconds/60:.1f} minutes ({wait_seconds:.0f} seconds)")
    
    # Test UTC conversion
    now_utc = datetime.now(timezone.utc)
    now_utc3 = now_utc + timedelta(hours=3)
    print(f"🌍 Current UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 Current UTC+3: {now_utc3.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True

async def test_grade_check_interval():
    """Test the grade check interval logic"""
    print("\n🔍 Testing Grade Check Interval Logic...")
    
    # Get interval from config
    interval_minutes = int(os.getenv("GRADE_CHECK_INTERVAL", "15"))
    interval_seconds = interval_minutes * 60
    
    print(f"⏰ Grade check interval: {interval_minutes} minutes ({interval_seconds} seconds)")
    
    # Test timing
    start_time = datetime.now()
    print(f"🕒 Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Simulate one interval
    await asyncio.sleep(2)  # Just wait 2 seconds for testing
    
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    print(f"🕒 End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ Elapsed: {elapsed:.1f} seconds")
    
    return True

async def test_scheduler_simulation():
    """Simulate the actual scheduler behavior"""
    print("\n🎯 Simulating Scheduler Behavior...")
    
    # Test quote scheduler
    print("📝 Quote Scheduler:")
    await test_quote_scheduler()
    
    # Test grade checker
    print("\n📊 Grade Checker:")
    await test_grade_check_interval()
    
    print("\n✅ All scheduler tests completed!")

if __name__ == "__main__":
    print("🚀 Starting Scheduled Tasks Test...")
    print("=" * 50)
    
    # Set test environment
    os.environ["QUOTE_SCHEDULE"] = "14:00"
    os.environ["GRADE_CHECK_INTERVAL"] = "15"
    
    asyncio.run(test_scheduler_simulation()) 