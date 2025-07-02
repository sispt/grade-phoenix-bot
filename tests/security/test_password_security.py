"""
🧪 Password Security Test Script
Test the password hashing and encryption functionality
"""
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.password_utils import (
    hash_password, verify_password, is_password_hashed
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_password_hashing():
    """Test password hashing functionality"""
    logger.info("🔐 Testing Password Hashing...")
    
    # Test basic hashing
    password = "test_password_123"
    hashed = hash_password(password)
    
    # Verify the hash looks correct
    assert hashed.startswith('$2b$'), "Hash should start with $2b$"
    assert len(hashed) == 60, "bcrypt hash should be 60 characters"
    
    # Test verification
    assert verify_password(password, hashed), "Password verification should succeed"
    assert not verify_password("wrong_password", hashed), "Wrong password should fail"
    
    # Test hash detection
    assert is_password_hashed(hashed), "Should detect hashed password"
    assert not is_password_hashed(password), "Should not detect plain password as hashed"
    
    logger.info("✅ Password hashing tests passed")

def test_password_hashing_edge_cases():
    """Test password hashing edge cases"""
    logger.info("🔐 Testing Password Hashing Edge Cases...")
    
    # Test that different hashes of same password are different (due to salt)
    password = "test_password_123"
    hashed1 = hash_password(password)
    hashed2 = hash_password(password)
    assert hashed1 != hashed2, "Different hashes should be different due to salt"
    
    # But both should verify correctly
    assert verify_password(password, hashed1), "First hash should verify"
    assert verify_password(password, hashed2), "Second hash should verify"
    
    logger.info("✅ Password hashing edge cases tests passed")

def test_edge_cases():
    """Test edge cases and error handling"""
    logger.info("🔐 Testing Edge Cases...")
    
    # Test empty password
    try:
        hashed = hash_password("")
        assert verify_password("", hashed), "Empty password should verify"
        logger.info("✅ Empty password handling works")
    except Exception as e:
        logger.error(f"❌ Empty password test failed: {e}")
        return False
    
    # Test special characters
    special_password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    try:
        hashed = hash_password(special_password)
        assert verify_password(special_password, hashed), "Special characters should verify"
        logger.info("✅ Special characters handling works")
    except Exception as e:
        logger.error(f"❌ Special characters test failed: {e}")
        return False
    
    # Test unicode characters
    unicode_password = "كلمة_المرور_العربية_123"
    try:
        hashed = hash_password(unicode_password)
        assert verify_password(unicode_password, hashed), "Unicode characters should verify"
        logger.info("✅ Unicode characters handling works")
    except Exception as e:
        logger.error(f"❌ Unicode characters test failed: {e}")
        return False
    
    return True

def test_integration():
    """Test integration between hashing and verification"""
    logger.info("🔐 Testing Integration...")
    
    password = "integration_test_password"
    
    # Test that we can hash and verify the same password
    hashed = hash_password(password)
    
    # Should work correctly
    assert verify_password(password, hashed), "Hashed password should verify"
    assert not verify_password("wrong_password", hashed), "Wrong password should not verify"
    
    # Test hash detection
    assert is_password_hashed(hashed), "Should detect hashed password"
    assert not is_password_hashed(password), "Should not detect plain password as hashed"
    
    logger.info("✅ Integration tests passed")

def main():
    """Run all password security tests"""
    logger.info("🧪 Starting Password Security Tests")
    logger.info("=" * 50)
    
    try:
        test_password_hashing()
        test_password_hashing_edge_cases()
        if test_edge_cases():
            test_integration()
        else:
            logger.error("❌ Edge case tests failed")
            return False
        
        logger.info("=" * 50)
        logger.info("✅ All password security tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 