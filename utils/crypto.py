import os
from cryptography.fernet import Fernet, InvalidToken
import base64
import logging

logger = logging.getLogger(__name__)

# You can set this in your config.py or as an environment variable
PASSWORD_ENCRYPTION_KEY = os.getenv("PASSWORD_ENCRYPTION_KEY")

# Generate a fallback key if none is provided (for development/testing)
if not PASSWORD_ENCRYPTION_KEY:
    logger.warning("⚠️ PASSWORD_ENCRYPTION_KEY not set. Generating a temporary key for this session.")
    PASSWORD_ENCRYPTION_KEY = Fernet.generate_key().decode()

# Ensure the key is properly formatted
try:
    fernet = Fernet(PASSWORD_ENCRYPTION_KEY.encode() if isinstance(PASSWORD_ENCRYPTION_KEY, str) else PASSWORD_ENCRYPTION_KEY)
    logger.info("✅ Password encryption initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize password encryption: {e}")
    # Create a fallback that will fail gracefully
    fernet = None

def encrypt_password(password: str) -> str:
    """Encrypt a password string using Fernet."""
    if not fernet:
        raise RuntimeError("Password encryption not available")
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(token: str) -> str:
    """Decrypt a Fernet-encrypted password string."""
    if not fernet:
        raise RuntimeError("Password encryption not available")
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        raise ValueError("Invalid encryption token or key.") 