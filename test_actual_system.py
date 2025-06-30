#!/usr/bin/env python3
"""
Test Actual System - See what the university system actually returns
"""
import asyncio
import aiohttp
import json
import logging
from bs4 import BeautifulSoup
from config import CONFIG

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_actual_system():
    """Test what the actual university system returns"""
    logger.info("🔍 Testing actual university system...")
    
    api_url = CONFIG["UNIVERSITY_API_URL"]
    headers = CONFIG["API_HEADERS"]
    
    logger.info(f"🌐 API URL: {api_url}")
    
    # Test 1: Simple GraphQL query
    logger.info("🧪 Test 1: Simple GraphQL query...")
    
    simple_query = """
    query {
        __typename
    }
    """
    
    payload = {
        "query": simple_query
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=payload) as response:
                logger.info(f"📡 Status: {response.status}")
                logger.info(f"📋 Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                
                response_text = await response.text()
                logger.info(f"📄 Response length: {len(response_text)} characters")
                
                if 'text/html' in response.headers.get('Content-Type', '').lower():
                    logger.info("📄 Got HTML response, analyzing content...")
                    
                    # Parse HTML to see what's in it
                    soup = BeautifulSoup(response_text, 'html.parser')
                    
                    # Look for forms (might be login forms)
                    forms = soup.find_all('form')
                    logger.info(f"📋 Found {len(forms)} forms")
                    
                    for i, form in enumerate(forms):
                        logger.info(f"📋 Form {i+1}: action='{form.get('action', 'None')}' method='{form.get('method', 'None')}'")
                        inputs = form.find_all('input')
                        for inp in inputs:
                            logger.info(f"  📝 Input: name='{inp.get('name', 'None')}' type='{inp.get('type', 'None')}'")
                    
                    # Look for tables (might contain grades)
                    tables = soup.find_all('table')
                    logger.info(f"📋 Found {len(tables)} tables")
                    
                    for i, table in enumerate(tables):
                        table_text = table.get_text()[:200]
                        logger.info(f"📋 Table {i+1} preview: {table_text}...")
                    
                    # Look for any text that might indicate what this page is
                    page_title = soup.find('title')
                    if page_title:
                        logger.info(f"📄 Page title: {page_title.get_text()}")
                    
                    # Look for error messages or login prompts
                    error_messages = soup.find_all(text=lambda text: text and any(keyword in text.lower() for keyword in ['error', 'login', 'auth', 'unauthorized', 'forbidden']))
                    if error_messages:
                        logger.info(f"⚠️ Found potential error messages: {error_messages[:3]}")
                    
                    # Look for any JavaScript that might give us clues
                    scripts = soup.find_all('script')
                    logger.info(f"📋 Found {len(scripts)} script tags")
                    
                    for i, script in enumerate(scripts):
                        if script.string:
                            script_content = script.string[:200]
                            if 'graphql' in script_content.lower() or 'api' in script_content.lower():
                                logger.info(f"📋 Script {i+1} (API related): {script_content}...")
                
                else:
                    logger.info(f"📄 Response preview: {response_text[:500]}...")
                    
    except Exception as e:
        logger.error(f"❌ Error: {e}")

async def test_different_approaches():
    """Test different approaches to get course data"""
    logger.info("🧪 Testing different approaches...")
    
    base_url = "https://staging.sis.shamuniversity.com"
    headers = CONFIG["API_HEADERS"]
    
    # Test different endpoints and methods
    tests = [
        ("GET", "/portal", "Basic portal access"),
        ("GET", "/portal/grades", "Direct grades page"),
        ("GET", "/portal/student", "Student portal"),
        ("POST", "/portal/graphql", "GraphQL endpoint"),
        ("GET", "/api/student/grades", "REST API grades"),
    ]
    
    for method, endpoint, description in tests:
        logger.info(f"🧪 {description}: {method} {endpoint}")
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(base_url + endpoint, headers=headers) as response:
                        logger.info(f"📡 Status: {response.status}")
                        logger.info(f"📋 Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                        
                        if response.status == 200:
                            response_text = await response.text()
                            logger.info(f"📄 Length: {len(response_text)} chars")
                            logger.info(f"📄 Preview: {response_text[:200]}...")
                        else:
                            logger.info(f"❌ Failed: {response.status}")
                
                elif method == "POST":
                    payload = {"query": "{ __typename }"}
                    async with session.post(base_url + endpoint, headers=headers, json=payload) as response:
                        logger.info(f"📡 Status: {response.status}")
                        logger.info(f"📋 Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                        
                        if response.status == 200:
                            response_text = await response.text()
                            logger.info(f"📄 Length: {len(response_text)} chars")
                            logger.info(f"📄 Preview: {response_text[:200]}...")
                        else:
                            logger.info(f"❌ Failed: {response.status}")
                            
        except Exception as e:
            logger.error(f"❌ Error: {e}")

async def main():
    """Main test function"""
    logger.info("🚀 Starting Actual System Test")
    logger.info("=" * 50)
    
    await test_actual_system()
    
    logger.info("=" * 50)
    await test_different_approaches()
    
    logger.info("=" * 50)
    logger.info("🎉 Actual system test completed!")
    logger.info("📊 Check the logs above to understand the university system")

if __name__ == "__main__":
    asyncio.run(main()) 