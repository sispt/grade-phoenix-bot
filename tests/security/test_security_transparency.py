#!/usr/bin/env python3
"""
🧪 Security Transparency Test Script
Test the security transparency and trust-building features
"""
import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from security.transparency import SecurityTransparency

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_security_transparency_initialization():
    """Test security transparency module initialization"""
    logger.info("🔐 Testing Security Transparency Initialization...")
    
    try:
        security = SecurityTransparency()
        
        # Test that security info is loaded
        assert security.security_info is not None, "Security info should be loaded"
        assert security.trust_indicators is not None, "Trust indicators should be loaded"
        
        # Test required fields
        assert 'version' in security.security_info, "Version should be present"
        assert 'security_rating' in security.security_info, "Security rating should be present"
        assert 'compliance' in security.security_info, "Compliance info should be present"
        
        logger.info("✅ Security transparency initialization tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security transparency initialization failed: {e}")
        return False

def test_security_welcome_messages():
    """Test security welcome messages"""
    logger.info("🔐 Testing Security Welcome Messages...")
    
    try:
        security = SecurityTransparency()
        
        # Test Arabic welcome message
        arabic_welcome = security.get_security_welcome_message('ar')
        assert '🔐' in arabic_welcome, "Arabic welcome should contain security emoji"
        assert 'عالي' in arabic_welcome, "Arabic welcome should mention high security level"
        assert 'التوافق مع المعايير' in arabic_welcome, "Arabic welcome should mention standards compliance"
        assert '/security_info' in arabic_welcome, "Arabic welcome should mention security commands"
        
        # Test English welcome message
        english_welcome = security.get_security_welcome_message('en')
        assert '🔐' in english_welcome, "English welcome should contain security emoji"
        assert 'High' in english_welcome, "English welcome should mention high security level"
        assert 'Standards Compliance' in english_welcome, "English welcome should mention standards compliance"
        assert '/security_info' in english_welcome, "English welcome should mention security commands"
        
        logger.info("✅ Security welcome message tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security welcome message tests failed: {e}")
        return False

def test_detailed_security_info():
    """Test detailed security information"""
    logger.info("🔐 Testing Detailed Security Information...")
    
    try:
        security = SecurityTransparency()
        
        # Test Arabic detailed info
        arabic_info = security.get_detailed_security_info('ar')
        assert '🔐' in arabic_info, "Arabic detailed info should contain security emoji"
        assert 'bcrypt' in arabic_info, "Arabic detailed info should mention bcrypt"
        assert 'OWASP' in arabic_info, "Arabic detailed info should mention OWASP"
        assert 'NIST' in arabic_info, "Arabic detailed info should mention NIST"
        assert 'GDPR' in arabic_info, "Arabic detailed info should mention GDPR"
        
        # Test English detailed info
        english_info = security.get_detailed_security_info('en')
        assert '🔐' in english_info, "English detailed info should contain security emoji"
        assert 'bcrypt' in english_info, "English detailed info should mention bcrypt"
        assert 'OWASP' in english_info, "English detailed info should mention OWASP"
        assert 'NIST' in english_info, "English detailed info should mention NIST"
        assert 'GDPR' in english_info, "English detailed info should mention GDPR"
        
        logger.info("✅ Detailed security info tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Detailed security info tests failed: {e}")
        return False

def test_security_audit_summary():
    """Test security audit summary"""
    logger.info("🔐 Testing Security Audit Summary...")
    
    try:
        security = SecurityTransparency()
        
        # Test Arabic audit summary
        arabic_audit = security.get_security_audit_summary('ar')
        assert '📋' in arabic_audit, "Arabic audit should contain document emoji"
        assert 'OWASP' in arabic_audit, "Arabic audit should mention OWASP"
        assert 'NIST' in arabic_audit, "Arabic audit should mention NIST"
        assert 'GDPR' in arabic_audit, "Arabic audit should mention GDPR"
        
        # Test English audit summary
        english_audit = security.get_security_audit_summary('en')
        assert '📋' in english_audit, "English audit should contain document emoji"
        assert 'OWASP' in english_audit, "English audit should mention OWASP"
        assert 'NIST' in english_audit, "English audit should mention NIST"
        assert 'GDPR' in english_audit, "English audit should mention GDPR"
        
        logger.info("✅ Security audit summary tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security audit summary tests failed: {e}")
        return False

def test_privacy_policy():
    """Test privacy policy"""
    logger.info("🔐 Testing Privacy Policy...")
    
    try:
        security = SecurityTransparency()
        
        # Test Arabic privacy policy
        arabic_policy = security.get_privacy_policy('ar')
        assert '🔒' in arabic_policy, "Arabic privacy policy should contain lock emoji"
        assert 'GDPR' in arabic_policy or 'خصوصية' in arabic_policy, "Arabic privacy policy should mention GDPR or privacy"
        assert 'bcrypt' in arabic_policy, "Arabic privacy policy should mention bcrypt"
        assert '@sisp_t' in arabic_policy, "Arabic privacy policy should contain contact info"
        
        # Test English privacy policy
        english_policy = security.get_privacy_policy('en')
        assert '🔒' in english_policy, "English privacy policy should contain lock emoji"
        assert 'GDPR' in english_policy or 'Privacy' in english_policy, "English privacy policy should mention GDPR or privacy"
        assert 'bcrypt' in english_policy, "English privacy policy should mention bcrypt"
        assert '@sisp_t' in english_policy, "English privacy policy should contain contact info"
        
        logger.info("✅ Privacy policy tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Privacy policy tests failed: {e}")
        return False

def test_security_badge():
    """Test security badge"""
    logger.info("🔐 Testing Security Badge...")
    
    try:
        security = SecurityTransparency()
        
        badge = security.get_security_badge()
        assert '🔐' in badge, "Security badge should contain security emoji"
        assert 'OWASP' in badge, "Security badge should mention OWASP"
        assert 'NIST' in badge, "Security badge should mention NIST"
        assert 'GDPR' in badge, "Security badge should mention GDPR"
        assert 'bcrypt' in badge, "Security badge should mention bcrypt"
        assert 'SQL' in badge, "Security badge should mention SQL protection"
        assert 'XSS' in badge, "Security badge should mention XSS protection"
        
        logger.info("✅ Security badge tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security badge tests failed: {e}")
        return False

def test_security_implementation_verification():
    """Test security implementation verification"""
    logger.info("🔐 Testing Security Implementation Verification...")
    
    try:
        security = SecurityTransparency()
        
        verification = security.verify_security_implementation()
        
        # Test that verification returns a dictionary
        assert isinstance(verification, dict), "Verification should return a dictionary"
        
        # Test that all expected keys are present
        expected_keys = [
            'bcrypt_available',
            'environment_variables', 
            'input_validation',
            'sql_injection_protection',
            'xss_protection',
            'secure_storage'
        ]
        
        for key in expected_keys:
            assert key in verification, f"Verification should contain {key}"
            assert isinstance(verification[key], bool), f"{key} should be a boolean"
        
        logger.info("✅ Security implementation verification tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security implementation verification tests failed: {e}")
        return False

def test_language_support():
    """Test language support for all messages"""
    logger.info("🔐 Testing Language Support...")
    
    try:
        security = SecurityTransparency()
        
        # Test that both Arabic and English work for all message types
        message_types = [
            'get_security_welcome_message',
            'get_detailed_security_info', 
            'get_security_audit_summary',
            'get_privacy_policy'
        ]
        
        for message_type in message_types:
            method = getattr(security, message_type)
            
            # Test Arabic
            arabic_msg = method('ar')
            assert len(arabic_msg) > 0, f"Arabic {message_type} should not be empty"
            
            # Test English
            english_msg = method('en')
            assert len(english_msg) > 0, f"English {message_type} should not be empty"
            
            # Test that messages are different (not just defaulting to one language)
            assert arabic_msg != english_msg, f"{message_type} should have different content for different languages"
        
        logger.info("✅ Language support tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Language support tests failed: {e}")
        return False

def test_content_quality():
    """Test content quality and completeness"""
    logger.info("🔐 Testing Content Quality...")
    
    try:
        security = SecurityTransparency()
        
        # Test that security info contains all required information
        info = security.security_info
        
        # Check version
        from config import CONFIG
        expected_version = CONFIG.get('BOT_VERSION', '2.5.7')
        assert info['version'] == expected_version, f"Version should match current version ({expected_version})"
        
        # Check security rating
        assert 'A+' in info['security_rating'], "Security rating should be A+"
        
        # Check compliance info
        compliance = info['compliance']
        assert 'owasp_top_10' in compliance, "OWASP compliance should be present"
        assert 'nist_framework' in compliance, "NIST compliance should be present"
        assert 'iso_27001' in compliance, "ISO 27001 compliance should be present"
        assert 'gdpr' in compliance, "GDPR compliance should be present"
        
        # Check security features
        features = info['security_features']
        assert 'bcrypt Password Hashing' in features, "bcrypt should be in features"
        assert 'SQL Injection Prevention' in features, "SQL injection prevention should be in features"
        assert 'XSS Protection' in features, "XSS protection should be in features"
        
        # Check trust indicators
        indicators = security.trust_indicators
        
        # Check password security
        password_sec = indicators['password_security']
        assert password_sec['algorithm'] == 'bcrypt', "Password algorithm should be bcrypt"
        assert password_sec['salt_generation'] == 'Automatic', "Salt generation should be automatic"
        assert password_sec['recovery'] == 'Impossible (One-way)', "Password recovery should be impossible"
        
        logger.info("✅ Content quality tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Content quality tests failed: {e}")
        return False

def main():
    """Run all security transparency tests"""
    logger.info("🧪 Starting Security Transparency Tests")
    logger.info("=" * 60)
    
    tests = [
        test_security_transparency_initialization,
        test_security_welcome_messages,
        test_detailed_security_info,
        test_security_audit_summary,
        test_privacy_policy,
        test_security_badge,
        test_security_implementation_verification,
        test_language_support,
        test_content_quality
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    logger.info("=" * 60)
    logger.info(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("✅ All security transparency tests passed!")
        logger.info("🔐 Security transparency features are working correctly")
        return True
    else:
        logger.error(f"❌ {failed} security transparency tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 