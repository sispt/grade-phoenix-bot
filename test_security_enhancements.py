#!/usr/bin/env python3
"""
🔐 Test Security Enhancements
Tests rate limiting, audit logging, and session management
"""
import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from security.enhancements import security_manager, RateLimiter, AuditLogger, SessionManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rate_limiting():
    """Test rate limiting functionality"""
    logger.info("🧪 Testing Rate Limiting...")
    
    try:
        rate_limiter = RateLimiter()
        
        # Test normal usage
        user_id = 12345
        assert rate_limiter.is_allowed(user_id), "User should be allowed initially"
        
        # Test multiple attempts (should allow 5 attempts)
        for i in range(5):
            rate_limiter.record_attempt(user_id, success=True)
            # After recording the attempt, check if still allowed for next attempt
            if i < 4:  # First 4 attempts should still allow the next one
                assert rate_limiter.is_allowed(user_id), f"User should be allowed after {i+1} attempts"
        
        # After 5 attempts, user should be blocked
        assert not rate_limiter.is_allowed(user_id), "User should be blocked after 5 attempts"
        
        # Test failed attempts count more
        rate_limiter = RateLimiter()
        rate_limiter.record_attempt(user_id, success=False)  # This counts as 3 attempts
        rate_limiter.record_attempt(user_id, success=False)  # This counts as 3 more attempts
        assert not rate_limiter.is_allowed(user_id), "User should be blocked after 2 failed attempts"
        
        logger.info("✅ Rate limiting tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rate limiting tests failed: {e}")
        return False

def test_audit_logging():
    """Test audit logging functionality"""
    logger.info("📝 Testing Audit Logging...")
    
    try:
        audit_logger = AuditLogger("test_audit.log")
        
        # Test logging events
        audit_logger.log_security_event(
            event_type="LOGIN_SUCCESS",
            user_id=12345,
            details={"username": "test_user"},
            success=True,
            risk_level="LOW"
        )
        
        audit_logger.log_security_event(
            event_type="LOGIN_FAILED",
            user_id=12345,
            details={"username": "test_user", "reason": "Invalid password"},
            success=False,
            risk_level="MEDIUM"
        )
        
        # Test getting events
        recent_events = audit_logger.get_recent_events(1)
        assert len(recent_events) >= 2, "Should have at least 2 recent events"
        
        login_events = audit_logger.get_events_by_type("LOGIN_SUCCESS")
        assert len(login_events) >= 1, "Should have at least 1 login success event"
        
        user_events = audit_logger.get_events_by_user(12345)
        assert len(user_events) >= 2, "Should have at least 2 events for user"
        
        logger.info("✅ Audit logging tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Audit logging tests failed: {e}")
        return False

def test_session_management():
    """Test session management functionality"""
    logger.info("🔑 Testing Session Management...")
    
    try:
        session_manager = SessionManager()
        
        # Test creating session
        user_id = 12345
        token = "test_token_123"
        user_data = {"username": "test_user", "fullname": "Test User"}
        
        session_id = session_manager.create_session(user_id, token, user_data)
        assert session_id is not None, "Session ID should be created"
        
        # Test getting session
        session = session_manager.get_session(user_id)
        assert session is not None, "Session should be retrievable"
        assert session['token'] == token, "Session should contain correct token"
        assert session['user_data']['username'] == "test_user", "Session should contain user data"
        
        # Test session activity update
        session_manager.update_session_activity(user_id)
        updated_session = session_manager.get_session(user_id)
        assert updated_session is not None, "Session should still be active after activity update"
        
        # Test session invalidation
        session_manager.invalidate_session(user_id)
        invalidated_session = session_manager.get_session(user_id)
        assert invalidated_session is None, "Session should be invalidated"
        
        logger.info("✅ Session management tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Session management tests failed: {e}")
        return False

def test_security_manager():
    """Test the main security manager"""
    logger.info("🛡️ Testing Security Manager...")
    
    try:
        # Test login attempt checking
        user_id = 12345
        assert security_manager.check_login_attempt(user_id), "Login attempt should be allowed initially"
        
        # Test recording login attempts
        security_manager.record_login_attempt(user_id, True, "test_user")
        security_manager.record_login_attempt(user_id, False, "test_user")
        
        # Test session creation
        token = "test_token_456"
        user_data = {"username": "test_user"}
        session_id = security_manager.create_user_session(user_id, token, user_data)
        assert session_id is not None, "Session should be created"
        
        # Test security stats
        stats = security_manager.get_security_stats()
        assert isinstance(stats, dict), "Security stats should be a dictionary"
        assert 'total_events_24h' in stats, "Stats should contain total events"
        assert 'failed_logins' in stats, "Stats should contain failed logins"
        
        logger.info("✅ Security manager tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security manager tests failed: {e}")
        return False

def test_welcome_messages():
    """Test the new welcome messages"""
    logger.info("👋 Testing Welcome Messages...")
    
    try:
        from utils.messages import get_simple_welcome_message, get_security_welcome_message, get_welcome_message
        
        # Test simple welcome message
        simple_welcome = get_simple_welcome_message()
        assert "مرحباً" in simple_welcome, "Simple welcome should contain greeting"
        assert "بوت متابعة الدرجات الجامعية" in simple_welcome, "Simple welcome should explain what the bot does"
        assert "🚀 تسجيل الدخول" in simple_welcome, "Simple welcome should mention login button"
        
        # Test security welcome message
        security_welcome = get_security_welcome_message()
        assert "مرحباً بعودتك" in security_welcome, "Security welcome should contain return greeting"
        assert "حالة الأمان" in security_welcome, "Security welcome should mention security status"
        assert "/security_info" in security_welcome, "Security welcome should mention security commands"
        
        # Test regular welcome message
        regular_welcome = get_welcome_message("Test User")
        assert "أهلاً Test User" in regular_welcome, "Regular welcome should include user name"
        assert "ما هو هذا البوت" in regular_welcome, "Regular welcome should explain what the bot does"
        assert "ماذا يمكنك أن تفعل" in regular_welcome, "Regular welcome should list features"
        
        logger.info("✅ Welcome message tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Welcome message tests failed: {e}")
        return False

async def main():
    """Run all security enhancement tests"""
    logger.info("🔐 Starting Security Enhancements Tests...")
    
    tests = [
        test_rate_limiting,
        test_audit_logging,
        test_session_management,
        test_security_manager,
        test_welcome_messages
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            logger.error(f"❌ Test {test.__name__} failed with exception: {e}")
    
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All security enhancement tests passed!")
        return True
    else:
        logger.error("❌ Some security enhancement tests failed!")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Test runner failed: {e}")
        sys.exit(1) 