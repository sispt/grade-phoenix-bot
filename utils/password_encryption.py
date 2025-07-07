"""
🔐 Password Encryption Utilities
Secure password storage using Fernet symmetric encryption
"""

import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional

logger = logging.getLogger(__name__)

class PasswordEncryption:
    """Secure password encryption using Fernet"""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize password encryption
        
        Args:
            secret_key: Optional secret key. If not provided, will use environment variable or generate new one
        """
        self.secret_key = secret_key or self._get_or_create_secret_key()
        self.fernet = Fernet(self.secret_key.encode())
        
    def _get_or_create_secret_key(self) -> str:
        """Get secret key from environment or create new one"""
        # Try to get from environment variable
        env_key = os.getenv('PASSWORD_ENCRYPTION_KEY')
        if env_key:
            logger.info("✅ Using password encryption key from environment")
            return env_key
            
        # Try to read from file
        key_file = "data/encryption_key.txt"
        try:
            if os.path.exists(key_file):
                with open(key_file, 'r') as f:
                    key = f.read().strip()
                    logger.info("✅ Using password encryption key from file")
                    return key
        except Exception as e:
            logger.warning(f"⚠️ Could not read encryption key from file: {e}")
        
        # Generate new key
        logger.info("🔑 Generating new password encryption key")
        key = Fernet.generate_key().decode()
        
        # Save to file for future use
        try:
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'w') as f:
                f.write(key)
            logger.info(f"✅ Saved new encryption key to {key_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save encryption key: {e}")
            
        return key
    
    def encrypt_password(self, password: str) -> str:
        """
        Encrypt a password securely
        
        Args:
            password: Plain text password
            
        Returns:
            Encrypted password as base64 string
        """
        try:
            if not password:
                return ""
                
            # Encrypt the password
            encrypted_data = self.fernet.encrypt(password.encode())
            
            # Return as base64 string
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"❌ Failed to encrypt password: {e}")
            raise ValueError("Password encryption failed")
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """
        Decrypt a password
        
        Args:
            encrypted_password: Encrypted password as base64 string
            
        Returns:
            Decrypted password
        """
        try:
            if not encrypted_password:
                return ""
                
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_password.encode())
            
            # Decrypt
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"❌ Failed to decrypt password: {e}")
            raise ValueError("Password decryption failed")
    
    def test_encryption(self) -> bool:
        """Test encryption/decryption functionality"""
        try:
            test_password = "test_password_123"
            encrypted = self.encrypt_password(test_password)
            decrypted = self.decrypt_password(encrypted)
            
            success = test_password == decrypted
            if success:
                logger.info("✅ Password encryption test passed")
            else:
                logger.error("❌ Password encryption test failed")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Password encryption test failed: {e}")
            return False

# Global instance
password_encryption = PasswordEncryption() 