#!/usr/bin/env python3
"""
Test imports to verify the project structure works correctly
"""
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports"""
    try:
        print("🧪 Testing imports...")
        
        # Test config
        from config import CONFIG
        print("✅ config imported successfully")
        
        # Test storage
        from storage.users import UserStorage
        from storage.grades import GradeStorage
        print("✅ storage modules imported successfully")
        
        # Test university API
        from university.api import UniversityAPI
        print("✅ university API imported successfully")
        
        # Test admin modules
        from admin.dashboard import AdminDashboard
        from admin.broadcast import BroadcastSystem
        print("✅ admin modules imported successfully")
        
        # Test utils
        from utils.keyboards import get_main_keyboard, get_admin_keyboard
        from utils.messages import get_welcome_message, get_help_message
        print("✅ utils modules imported successfully")
        
        # Test health server
        from health.server import HealthServer
        print("✅ health server imported successfully")
        
        # Test bot core
        from bot.core import TelegramBot
        print("✅ bot core imported successfully")
        
        print("🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("✅ Project structure is correct!")
    else:
        print("❌ There are import issues to fix!")
        sys.exit(1) 