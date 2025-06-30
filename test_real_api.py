#!/usr/bin/env python3
"""
Test Real API - Check what the university API actually returns
"""
import asyncio
import aiohttp
import json
import logging
from config import CONFIG, UNIVERSITY_QUERIES

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_university_api():
    """Test the university API to see what it returns"""
    logger.info("🔍 Testing university API responses...")
    
    api_url = CONFIG["UNIVERSITY_API_URL"]
    headers = CONFIG["API_HEADERS"]
    
    # Test 1: Simple introspection query
    logger.info("🧪 Test 1: API introspection...")
    
    introspection_query = """
    query IntrospectionQuery {
      __schema {
        types {
          name
          description
        }
      }
    }
    """
    
    payload = {
        "query": introspection_query
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=payload) as response:
                logger.info(f"📡 Introspection status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"📄 Introspection response keys: {list(data.keys())}")
                    
                    if "data" in data and data["data"]["__schema"]:
                        types = data["data"]["__schema"]["types"]
                        logger.info(f"📋 Found {len(types)} GraphQL types")
                        
                        # Look for grade-related types
                        grade_types = [t for t in types if t["name"] and any(keyword in t["name"].lower() for keyword in ["grade", "course", "student"])]
                        logger.info(f"📚 Grade-related types: {[t['name'] for t in grade_types]}")
                else:
                    logger.warning(f"⚠️ Introspection failed: {response.status}")
    except Exception as e:
        logger.error(f"❌ Introspection error: {e}")
    
    # Test 2: Try the course grades query
    logger.info("🧪 Test 2: Course grades query...")
    
    course_grades_payload = {
        "query": UNIVERSITY_QUERIES["GET_COURSE_GRADES"],
        "variables": {
            "t_grade_id": "1"
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=course_grades_payload) as response:
                logger.info(f"📡 Course grades status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"📄 Course grades response: {data}")
                else:
                    error_text = await response.text()
                    logger.warning(f"⚠️ Course grades failed: {error_text}")
    except Exception as e:
        logger.error(f"❌ Course grades error: {e}")
    
    # Test 3: Try the student courses query
    logger.info("🧪 Test 3: Student courses query...")
    
    student_courses_payload = {
        "query": UNIVERSITY_QUERIES["GET_STUDENT_COURSES"],
        "variables": {
            "t_grade_id": "1"
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=student_courses_payload) as response:
                logger.info(f"📡 Student courses status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"📄 Student courses response: {data}")
                else:
                    error_text = await response.text()
                    logger.warning(f"⚠️ Student courses failed: {error_text}")
    except Exception as e:
        logger.error(f"❌ Student courses error: {e}")

async def main():
    """Main test function"""
    logger.info("🚀 Starting Real API Test")
    logger.info("=" * 50)
    
    await test_university_api()
    
    logger.info("=" * 50)
    logger.info("🎉 Real API test completed!")
    logger.info("📊 Check the logs above to see what the API actually returns")

if __name__ == "__main__":
    asyncio.run(main()) 