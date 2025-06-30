#!/usr/bin/env python3
"""
Debug API Response - See what the university API actually returns
"""
import asyncio
import aiohttp
import json
import logging
from config import CONFIG

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_api_response():
    """Debug what the API actually returns"""
    logger.info("🔍 Debugging API response...")
    
    api_url = CONFIG["UNIVERSITY_API_URL"]
    headers = CONFIG["API_HEADERS"]
    
    logger.info(f"🌐 API URL: {api_url}")
    logger.info(f"📋 Headers: {headers}")
    
    # Simple test query
    test_query = """
    query {
        __typename
    }
    """
    
    payload = {
        "query": test_query
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=payload) as response:
                logger.info(f"📡 Response status: {response.status}")
                logger.info(f"📋 Response headers: {dict(response.headers)}")
                
                # Get content type
                content_type = response.headers.get('Content-Type', '')
                logger.info(f"📄 Content-Type: {content_type}")
                
                # Get the actual response text
                response_text = await response.text()
                logger.info(f"📄 Response length: {len(response_text)} characters")
                logger.info(f"📄 First 500 characters: {response_text[:500]}")
                
                if len(response_text) > 500:
                    logger.info(f"📄 Next 500 characters: {response_text[500:1000]}")
                
                if len(response_text) > 1000:
                    logger.info(f"📄 Next 500 characters: {response_text[1000:1500]}")
                
                # Try to parse as JSON
                try:
                    if 'application/json' in content_type.lower():
                        data = json.loads(response_text)
                        logger.info(f"✅ Successfully parsed JSON: {data}")
                    else:
                        logger.warning(f"⚠️ Content-Type is not JSON: {content_type}")
                        logger.info(f"📄 Full response text: {response_text}")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error: {e}")
                    logger.info(f"📄 Full response text: {response_text}")
                
    except Exception as e:
        logger.error(f"❌ Request error: {e}")

async def test_different_endpoints():
    """Test different possible endpoints"""
    logger.info("🧪 Testing different endpoints...")
    
    base_url = "https://staging.sis.shamuniversity.com"
    headers = CONFIG["API_HEADERS"]
    
    endpoints_to_test = [
        "/portal/graphql",
        "/graphql",
        "/api/graphql",
        "/portal",
        "/api"
    ]
    
    for endpoint in endpoints_to_test:
        url = base_url + endpoint
        logger.info(f"🌐 Testing: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json={"query": "{ __typename }"}) as response:
                    logger.info(f"📡 {endpoint} - Status: {response.status}")
                    logger.info(f"📋 {endpoint} - Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                    
                    if response.status == 200:
                        response_text = await response.text()
                        logger.info(f"📄 {endpoint} - First 200 chars: {response_text[:200]}")
        except Exception as e:
            logger.error(f"❌ {endpoint} - Error: {e}")

async def main():
    """Main debug function"""
    logger.info("🚀 Starting API Debug")
    logger.info("=" * 50)
    
    await debug_api_response()
    
    logger.info("=" * 50)
    await test_different_endpoints()
    
    logger.info("=" * 50)
    logger.info("🎉 Debug completed!")

if __name__ == "__main__":
    asyncio.run(main()) 