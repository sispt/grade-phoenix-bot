#!/usr/bin/env python3
"""
🧪 Bot Integration Test Suite
Tests all components for smooth user experience
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CONFIG
from storage.models import DatabaseManager
from storage.postgresql_users import PostgreSQLUserStorage
from storage.postgresql_grades import PostgreSQLGradeStorage
from storage.users import UserStorage
from storage.grades import GradeStorage
from university.api import UniversityAPI
from utils.keyboards import get_main_keyboard, get_main_keyboard_with_relogin
from utils.messages import get_welcome_message, get_help_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotIntegrationTest:
    """Comprehensive bot integration test suite"""
    
    def __init__(self):
        self.test_results = []
        self.test_user = {
            "telegram_id": 123456789,
            "username": "TEST_USER",
            "password": "test_password",
            "firstname": "اختبار",
            "lastname": "مستخدم",
            "fullname": "اختبار مستخدم",
            "email": "test@student.shamuniversity.com"
        }
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🧪 Starting Bot Integration Test Suite")
        logger.info("=" * 60)
        
        tests = [
            ("Configuration Test", self.test_configuration),
            ("Storage System Test", self.test_storage_system),
            ("University API Test", self.test_university_api),
            ("Message System Test", self.test_message_system),
            ("Keyboard System Test", self.test_keyboard_system),
            ("Database Migration Test", self.test_database_migration),
            ("Error Handling Test", self.test_error_handling),
            ("User Experience Test", self.test_user_experience)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n🔍 Running {test_name}...")
            try:
                result = await test_func()
                self.test_results.append((test_name, result, "PASSED"))
                logger.info(f"✅ {test_name}: PASSED")
            except Exception as e:
                self.test_results.append((test_name, str(e), "FAILED"))
                logger.error(f"❌ {test_name}: FAILED - {e}")
        
        await self.generate_test_report()
    
    async def test_configuration(self):
        """Test configuration system"""
        logger.info("Testing configuration...")
        
        # Check required config keys
        required_keys = [
            "TELEGRAM_TOKEN", "ADMIN_ID", "DATABASE_URL", 
            "UNIVERSITY_LOGIN_URL", "UNIVERSITY_API_URL"
        ]
        
        for key in required_keys:
            if key not in CONFIG:
                raise Exception(f"Missing required config key: {key}")
        
        # Check database configuration
        if CONFIG.get("USE_POSTGRESQL", False):
            if not CONFIG["DATABASE_URL"].startswith("postgresql"):
                raise Exception("Invalid PostgreSQL URL")
        
        logger.info("✅ Configuration test passed")
        return True
    
    async def test_storage_system(self):
        """Test storage system initialization"""
        logger.info("Testing storage system...")
        
        try:
            if CONFIG.get("USE_POSTGRESQL", False):
                # Test PostgreSQL storage
                db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
                if not db_manager.test_connection():
                    raise Exception("PostgreSQL connection failed")
                
                user_storage = PostgreSQLUserStorage(db_manager)
                grade_storage = PostgreSQLGradeStorage(db_manager)
                
                # Test basic operations
                user_storage.get_users_count()
                grade_storage.get_grades_summary()
                
            else:
                # Test file storage
                user_storage = UserStorage()
                grade_storage = GradeStorage()
                
                # Test basic operations
                user_storage.get_users_count()
                grade_storage.get_grades_summary()
            
            logger.info("✅ Storage system test passed")
            return True
            
        except Exception as e:
            raise Exception(f"Storage system test failed: {e}")
    
    async def test_university_api(self):
        """Test university API integration"""
        logger.info("Testing university API...")
        
        try:
            api = UniversityAPI()
            
            # Test API configuration
            if not api.login_url or not api.api_url:
                raise Exception("API URLs not configured")
            
            # Test headers configuration
            if not api.api_headers:
                raise Exception("API headers not configured")
            
            # Test timeout configuration
            if not api.timeout:
                raise Exception("API timeout not configured")
            
            logger.info("✅ University API test passed")
            return True
            
        except Exception as e:
            raise Exception(f"University API test failed: {e}")
    
    async def test_message_system(self):
        """Test message system"""
        logger.info("Testing message system...")
        
        try:
            # Test welcome message
            welcome_msg = get_welcome_message("Test User")
            if not welcome_msg or len(welcome_msg) < 50:
                raise Exception("Welcome message too short or empty")
            
            # Test help message
            help_msg = get_help_message()
            if not help_msg or len(help_msg) < 100:
                raise Exception("Help message too short or empty")
            
            # Test error messages
            from utils.messages import get_error_message, get_success_message, get_info_message
            
            error_msg = get_error_message("login_failed")
            success_msg = get_success_message("login")
            info_msg = get_info_message("not_registered")
            
            if not all([error_msg, success_msg, info_msg]):
                raise Exception("Message templates missing")
            
            logger.info("✅ Message system test passed")
            return True
            
        except Exception as e:
            raise Exception(f"Message system test failed: {e}")
    
    async def test_keyboard_system(self):
        """Test keyboard system"""
        logger.info("Testing keyboard system...")
        
        try:
            # Test main keyboard
            main_kb = get_main_keyboard()
            if not main_kb:
                raise Exception("Main keyboard not created")
            
            # Test keyboard with re-login
            relogin_kb = get_main_keyboard_with_relogin()
            if not relogin_kb:
                raise Exception("Re-login keyboard not created")
            
            # Test keyboard buttons
            keyboard_text = str(main_kb)
            required_buttons = ["🚀 تسجيل الدخول", "📊 فحص الدرجات", "👤 معلوماتي"]
            
            for button in required_buttons:
                if button not in keyboard_text:
                    raise Exception(f"Missing button: {button}")
            
            logger.info("✅ Keyboard system test passed")
            return True
            
        except Exception as e:
            raise Exception(f"Keyboard system test failed: {e}")
    
    async def test_database_migration(self):
        """Test database migration system"""
        logger.info("Testing database migration...")
        
        try:
            from migrations import run_migrations, check_database_status
            
            # Test migration function exists
            if not callable(run_migrations):
                raise Exception("Migration function not found")
            
            if not callable(check_database_status):
                raise Exception("Database status function not found")
            
            logger.info("✅ Database migration test passed")
            return True
            
        except Exception as e:
            raise Exception(f"Database migration test failed: {e}")
    
    async def test_error_handling(self):
        """Test error handling system"""
        logger.info("Testing error handling...")
        
        try:
            from utils.messages import get_error_message
            
            # Test various error types
            error_types = ["login_failed", "network_error", "api_error", "token_expired", "no_grades"]
            
            for error_type in error_types:
                error_msg = get_error_message(error_type)
                if not error_msg or len(error_msg) < 20:
                    raise Exception(f"Error message for {error_type} too short")
            
            logger.info("✅ Error handling test passed")
            return True
            
        except Exception as e:
            raise Exception(f"Error handling test failed: {e}")
    
    async def test_user_experience(self):
        """Test user experience features"""
        logger.info("Testing user experience...")
        
        try:
            # Test loading message configuration
            if not CONFIG.get("SHOW_LOADING_MESSAGES", True):
                logger.warning("Loading messages disabled")
            
            # Test typing indicator configuration
            if not CONFIG.get("ENABLE_TYPING_INDICATOR", True):
                logger.warning("Typing indicator disabled")
            
            # Test message timeout
            timeout = CONFIG.get("MESSAGE_TIMEOUT_SECONDS", 30)
            if timeout < 10 or timeout > 300:
                raise Exception("Invalid message timeout value")
            
            # Test max message length
            max_length = CONFIG.get("MAX_MESSAGE_LENGTH", 4096)
            if max_length < 1000 or max_length > 4096:
                raise Exception("Invalid max message length")
            
            logger.info("✅ User experience test passed")
            return True
            
        except Exception as e:
            raise Exception(f"User experience test failed: {e}")
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n📋 Generating Test Report...")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r[2] == "PASSED"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"📊 Test Results Summary:")
        logger.info(f"   • Total Tests: {total_tests}")
        logger.info(f"   • Passed: {passed_tests}")
        logger.info(f"   • Failed: {failed_tests}")
        logger.info(f"   • Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.error("\n❌ Failed Tests:")
            for test_name, error, status in self.test_results:
                if status == "FAILED":
                    logger.error(f"   • {test_name}: {error}")
        
        logger.info("\n✅ Passed Tests:")
        for test_name, result, status in self.test_results:
            if status == "PASSED":
                logger.info(f"   • {test_name}")
        
        # Overall assessment
        if failed_tests == 0:
            logger.info("\n🎉 ALL TESTS PASSED! Bot is ready for production.")
            logger.info("✅ User experience should be smooth and reliable.")
        elif failed_tests <= 2:
            logger.warning("\n⚠️ MOST TESTS PASSED. Minor issues detected.")
            logger.warning("🔧 Consider fixing failed tests before production.")
        else:
            logger.error("\n❌ MULTIPLE TESTS FAILED. Bot needs fixes before production.")
            logger.error("🔧 Fix all failed tests before deploying.")
        
        # Save report to file
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("Bot Integration Test Report\n")
            f.write("=" * 40 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Passed: {passed_tests}\n")
            f.write(f"Failed: {failed_tests}\n")
            f.write(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n\n")
            
            for test_name, result, status in self.test_results:
                f.write(f"{status}: {test_name}\n")
                if status == "FAILED":
                    f.write(f"  Error: {result}\n")
                f.write("\n")
        
        logger.info(f"📄 Test report saved to: {report_file}")

async def main():
    """Main test function"""
    print("🧪 Bot Integration Test Suite")
    print("=" * 40)
    
    tester = BotIntegrationTest()
    await tester.run_all_tests()
    
    print("\n" + "=" * 60)
    print("🎯 TESTING COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 