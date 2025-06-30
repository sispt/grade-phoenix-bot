#!/usr/bin/env python3
"""
🧪 Test script to verify Telegram bot authentication with GraphQL
"""
import asyncio
import logging
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from university.api import UniversityAPI
from config import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_bot_authentication():
    """Test the bot's authentication system"""
    print("🧪 Testing Telegram Bot Authentication")
    print("=" * 60)
    
    # Test credentials (replace with real ones)
    test_credentials = [
        ("ENG2425041", "0951202512"),
        # Add more test credentials here
    ]
    
    api = UniversityAPI()
    
    print(f"🔧 API Configuration:")
    print(f"   Login URL: {api.login_url}")
    print(f"   GraphQL URL: {api.api_url}")
    print(f"   Headers: {api.api_headers}")
    print()
    
    for username, password in test_credentials:
        print(f"🔐 Testing authentication for: {username}")
        print("-" * 40)
        
        try:
            # Step 1: Test login
            print("📡 Attempting login...")
            token = await api.login(username, password)
            
            if not token:
                print("❌ Login failed - no token received")
                continue
            
            print(f"✅ Login successful! Token: {token[:20]}...")
            
            # Step 2: Test token validity
            print("🔍 Testing token validity...")
            is_valid = await api.test_token(token)
            
            if not is_valid:
                print("❌ Token validation failed")
                continue
            
            print("✅ Token is valid!")
            
            # Step 3: Test user info retrieval
            print("👤 Fetching user information...")
            user_data = await api.get_user_data(token)
            
            if not user_data:
                print("❌ Failed to get user data")
                continue
            
            print("✅ User data retrieved successfully!")
            print(f"   Name: {user_data.get('fullname', 'N/A')}")
            print(f"   Email: {user_data.get('email', 'N/A')}")
            print(f"   Username: {user_data.get('username', 'N/A')}")
            
            # Step 4: Check grades
            grades = user_data.get('grades', [])
            print(f"📊 Grades: {len(grades)} courses found")
            
            if grades:
                print("   Sample grades:")
                for i, grade in enumerate(grades[:3]):  # Show first 3 grades
                    print(f"     {i+1}. {grade.get('name', 'N/A')} - {grade.get('total', 'N/A')}")
            
            print("🎉 All tests passed for this user!")
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            logger.error(f"Test error for {username}: {e}")
        
        print("\n" + "=" * 60 + "\n")
    
    print("🏁 Authentication testing completed!")

async def test_configuration():
    """Test the configuration is correct"""
    print("🔧 Testing Configuration")
    print("=" * 40)
    
    required_keys = [
        "UNIVERSITY_LOGIN_URL",
        "UNIVERSITY_API_URL", 
        "API_HEADERS"
    ]
    
    for key in required_keys:
        if key in CONFIG:
            print(f"✅ {key}: {CONFIG[key]}")
        else:
            print(f"❌ Missing: {key}")
    
    print()
    
    # Check headers structure
    headers = CONFIG.get("API_HEADERS", {})
    required_headers = ["User-Agent", "Content-Type", "x-lang", "Accept", "Origin", "Referer"]
    
    for header in required_headers:
        if header in headers:
            print(f"✅ Header {header}: {headers[header]}")
        else:
            print(f"❌ Missing header: {header}")
    
    print()

async def main():
    """Main function"""
    try:
        # Test configuration first
        await test_configuration()
        
        # Test authentication
        await test_bot_authentication()
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Main test error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 