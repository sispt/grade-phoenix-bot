#!/usr/bin/env python3
"""
Quick Fix Script for Telegram University Bot
"""
import subprocess
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_dependencies():
    """Install required dependencies"""
    logger.info("📦 Installing dependencies...")
    
    try:
        # Install requirements
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Dependencies installed successfully!")
            return True
        else:
            logger.error(f"❌ Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error installing dependencies: {e}")
        return False

def test_imports():
    """Test if all modules can be imported"""
    logger.info("🔍 Testing imports...")
    
    modules_to_test = [
        "telegram",
        "aiohttp", 
        "bs4",
        "flask",
        "sqlalchemy",
        "psycopg2"
    ]
    
    failed_imports = []
    
    for module in modules_to_test:
        try:
            __import__(module)
            logger.info(f"✅ {module} imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        logger.error(f"❌ Failed imports: {failed_imports}")
        return False
    else:
        logger.info("✅ All imports successful!")
        return True

def test_config():
    """Test configuration loading"""
    logger.info("🔍 Testing configuration...")
    
    try:
        from config import CONFIG
        logger.info("✅ Configuration loaded successfully!")
        logger.info(f"📋 Bot Version: {CONFIG.get('BOT_VERSION', 'Unknown')}")
        logger.info(f"🌐 API URL: {CONFIG.get('UNIVERSITY_API_URL', 'Unknown')}")
        return True
    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")
        return False

def test_api():
    """Test API connection"""
    logger.info("🔍 Testing API connection...")
    
    try:
        # Import and test API
        from university.api import UniversityAPI
        
        # Create API instance
        api = UniversityAPI()
        logger.info("✅ API class created successfully!")
        logger.info(f"🔗 Login URL: {api.login_url}")
        logger.info(f"🔗 API URL: {api.api_url}")
        
        return True
    except Exception as e:
        logger.error(f"❌ API test error: {e}")
        return False

def main():
    """Main fix function"""
    logger.info("🚀 Starting Quick Fix for Telegram University Bot")
    logger.info("=" * 60)
    
    # Step 1: Install dependencies
    deps_ok = install_dependencies()
    
    # Step 2: Test imports
    imports_ok = test_imports()
    
    # Step 3: Test configuration
    config_ok = test_config()
    
    # Step 4: Test API
    api_ok = test_api()
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 Quick Fix Results:")
    logger.info(f"Dependencies: {'✅ PASS' if deps_ok else '❌ FAIL'}")
    logger.info(f"Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    logger.info(f"Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    logger.info(f"API: {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    all_passed = deps_ok and imports_ok and config_ok and api_ok
    
    if all_passed:
        logger.info("🎉 Quick fix completed successfully!")
        logger.info("🚀 Bot should now work properly!")
        
        # Run API test
        logger.info("🔍 Running API connection test...")
        try:
            subprocess.run([sys.executable, "test_api_simple.py"])
        except Exception as e:
            logger.error(f"❌ API test failed: {e}")
    else:
        logger.info("⚠️ Some issues remain. Check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 