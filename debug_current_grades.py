#!/usr/bin/env python3
"""
Debug script to test current grades functionality
"""

import asyncio
import logging
from university.api_client import UniversityAPI
from storage.user_storage import PostgreSQLUserStorage
from storage.models import DatabaseManager
from config import CONFIG

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_current_grades():
    """Test current grades functionality"""
    try:
        # Initialize API and storage
        api = UniversityAPI()
        
        # Initialize PostgreSQL storage
        db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
        user_storage = PostgreSQLUserStorage(db_manager)
        
        # Get a test user (you'll need to replace with a real user ID)
        test_user_id = 6850052552  # From the logs
        user = user_storage.get_user(test_user_id)
        
        if not user:
            logger.error("❌ Test user not found")
            return
            
        token = user.get("token")
        if not token:
            logger.error("❌ No token found for test user")
            return
            
        logger.info(f"🔍 Testing current grades for user {test_user_id}")
        
        # Test 1: Direct get_current_grades call
        logger.info("📊 Testing get_current_grades directly...")
        current_grades = await api.get_current_grades(token)
        logger.info(f"Current grades result: {current_grades}")
        
        if current_grades:
            logger.info(f"✅ Found {len(current_grades)} current grades")
            for grade in current_grades[:3]:  # Show first 3
                logger.info(f"  - {grade.get('name', 'N/A')}: {grade.get('total', 'N/A')}")
        else:
            logger.warning("⚠️ No current grades found")
        
        # Test 2: get_user_data call (what the bot actually uses)
        logger.info("📊 Testing get_user_data...")
        user_data = await api.get_user_data(token)
        logger.info(f"User data result: {user_data is not None}")
        
        if user_data:
            grades = user_data.get("grades", [])
            logger.info(f"Grades from user_data: {len(grades) if grades else 0}")
            if grades:
                for grade in grades[:3]:  # Show first 3
                    logger.info(f"  - {grade.get('name', 'N/A')}: {grade.get('total', 'N/A')}")
            else:
                logger.warning("⚠️ No grades in user_data")
        else:
            logger.error("❌ No user_data returned")
        
        # Test 3: Test old grades for comparison
        logger.info("📚 Testing old grades for comparison...")
        old_grades = await api.get_old_grades(token)
        logger.info(f"Old grades result: {len(old_grades) if old_grades else 0}")
        
        if old_grades:
            for grade in old_grades[:3]:  # Show first 3
                logger.info(f"  - {grade.get('name', 'N/A')}: {grade.get('total', 'N/A')}")
        
    except Exception as e:
        logger.error(f"❌ Error in test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_current_grades()) 