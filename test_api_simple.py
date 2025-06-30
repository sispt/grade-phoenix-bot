#!/usr/bin/env python3
"""
Simple API Test for University Bot
"""
import asyncio
import aiohttp
import json
import logging
from config import CONFIG

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_api_connection():
    """Test basic API connection"""
    logger.info("🔍 Testing API connection...")
    
    # Test URL
    test_url = CONFIG["UNIVERSITY_API_URL"]
    headers = CONFIG["API_HEADERS"]
    
    # Simple GraphQL query
    payload = {
        "query": """
        query {
            __typename
        }
        """
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(test_url, headers=headers, json=payload) as response:
                logger.info(f"Status: {response.status}")
                logger.info(f"Headers: {dict(response.headers)}")
                
                content_type = response.headers.get('Content-Type', '')
                logger.info(f"Content-Type: {content_type}")
                
                response_text = await response.text()
                logger.info(f"Response: {response_text[:500]}")
                
                if response.status == 200:
                    logger.info("✅ API connection successful!")
                    return True
                else:
                    logger.error(f"❌ API connection failed: {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ API test error: {e}")
        return False

async def test_login_endpoint():
    """Test login endpoint structure"""
    logger.info("🔍 Testing login endpoint...")
    
    login_url = CONFIG["UNIVERSITY_LOGIN_URL"]
    headers = CONFIG["API_HEADERS"]
    
    # Test login mutation structure
    payload = {
        "operationName": "signinUser",
        "variables": {
            "username": "test_user",
            "password": "test_pass"
        },
        "query": CONFIG["UNIVERSITY_QUERIES"]["LOGIN"]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(login_url, headers=headers, json=payload) as response:
                logger.info(f"Login Status: {response.status}")
                logger.info(f"Login Headers: {dict(response.headers)}")
                
                content_type = response.headers.get('Content-Type', '')
                logger.info(f"Login Content-Type: {content_type}")
                
                response_text = await response.text()
                logger.info(f"Login Response: {response_text[:500]}")
                
                if response.status == 200:
                    logger.info("✅ Login endpoint accessible!")
                    return True
                elif response.status == 401:
                    logger.info("✅ Login endpoint working (expected 401 for invalid credentials)")
                    return True
                else:
                    logger.error(f"❌ Login endpoint failed: {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Login test error: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting Simple API Tests")
    logger.info("=" * 50)
    
    # Test 1: Basic API connection
    api_ok = await test_api_connection()
    
    # Test 2: Login endpoint
    login_ok = await test_login_endpoint()
    
    # Summary
    logger.info("=" * 50)
    logger.info("📊 Test Results:")
    logger.info(f"API Connection: {'✅ PASS' if api_ok else '❌ FAIL'}")
    logger.info(f"Login Endpoint: {'✅ PASS' if login_ok else '❌ FAIL'}")
    
    if api_ok and login_ok:
        logger.info("🎉 All tests passed! API configuration looks good.")
    else:
        logger.info("⚠️ Some tests failed. Check configuration.")

if __name__ == "__main__":
    asyncio.run(main()) 