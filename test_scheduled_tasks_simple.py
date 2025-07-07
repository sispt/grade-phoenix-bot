#!/usr/bin/env python3
"""
Simple test for scheduled tasks
"""

import asyncio
import os
import time
from datetime import datetime, timedelta, timezone

async def test_grade_check_loop():
    """Test the grade checking loop logic"""
    print("🔍 Testing Grade Check Loop...")
    
    # Simulate the actual loop
    running = True
    check_count = 0
    max_checks = 3  # Only run 3 checks for testing
    
    while running and check_count < max_checks:
        try:
            print(f"🔔 Running scheduled grade check #{check_count + 1}...")
            # Simulate grade check work
            await asyncio.sleep(1)
            print(f"✅ Grade check #{check_count + 1} completed")
            check_count += 1
            
            # Wait for interval (shortened for testing)
            interval = 5  # 5 seconds for testing instead of 15 minutes
            print(f"⏳ Waiting {interval} seconds before next check...")
            await asyncio.sleep(interval)
            
        except Exception as e:
            print(f"❌ Error in scheduled grade check: {e}")
            break
    
    print("✅ Grade check loop test completed!")

async def test_quote_scheduler():
    """Test the quote scheduler logic"""
    print("🔍 Testing Quote Scheduler...")
    
    # Simulate the actual scheduler
    running = True
    quote_count = 0
    max_quotes = 2  # Only run 2 quotes for testing
    
    while running and quote_count < max_quotes:
        try:
            print(f"💬 Running scheduled quote broadcast #{quote_count + 1}...")
            # Simulate quote work
            await asyncio.sleep(1)
            print(f"✅ Quote broadcast #{quote_count + 1} completed")
            quote_count += 1
            
            # Wait for next day (shortened for testing)
            wait_time = 3  # 3 seconds for testing instead of 24 hours
            print(f"⏳ Waiting {wait_time} seconds before next quote...")
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            print(f"❌ Error in scheduled quote broadcast: {e}")
            break
    
    print("✅ Quote scheduler test completed!")

async def test_both_schedulers():
    """Test both schedulers running concurrently"""
    print("🚀 Testing Both Scheduled Tasks Concurrently...")
    print("=" * 50)
    
    # Start both tasks
    grade_task = asyncio.create_task(test_grade_check_loop())
    quote_task = asyncio.create_task(test_quote_scheduler())
    
    # Wait for both to complete
    await asyncio.gather(grade_task, quote_task)
    
    print("\n✅ All scheduled task tests completed!")

if __name__ == "__main__":
    print("🎯 Starting Simple Scheduled Tasks Test...")
    asyncio.run(test_both_schedulers()) 