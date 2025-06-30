#!/usr/bin/env python3
"""
Quick test to verify UNIVERSITY_QUERIES import fix
"""
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all imports work correctly"""
    try:
        logger.info("🔍 Testing imports...")
        
        # Test config import
        from config import CONFIG, UNIVERSITY_QUERIES
        logger.info("✅ CONFIG and UNIVERSITY_QUERIES imported successfully")
        
        # Test university API import
        from university.api import UniversityAPI
        logger.info("✅ UniversityAPI imported successfully")
        
        # Test UNIVERSITY_QUERIES content
        logger.info(f"📋 UNIVERSITY_QUERIES keys: {list(UNIVERSITY_QUERIES.keys())}")
        
        # Test specific queries
        login_query = UNIVERSITY_QUERIES["LOGIN"]
        logger.info(f"🔐 LOGIN query: {login_query[:100]}...")
        
        user_info_query = UNIVERSITY_QUERIES["GET_USER_INFO"]
        logger.info(f"👤 GET_USER_INFO query: {user_info_query[:100]}...")
        
        # Test API class creation
        api = UniversityAPI()
        logger.info("✅ UniversityAPI instance created successfully")
        logger.info(f"🔗 Login URL: {api.login_url}")
        logger.info(f"🔗 API URL: {api.api_url}")
        
        logger.info("🎉 All tests passed! The fix is working correctly.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 