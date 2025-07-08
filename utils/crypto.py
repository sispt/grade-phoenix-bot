import os
from cryptography.fernet import Fernet, InvalidToken

# You can set this in your config.py or as an environment variable
PASSWORD_ENCRYPTION_KEY = os.getenv(
    "PASSWORD_ENCRYPTION_KEY"
)

fernet = Fernet(PASSWORD_ENCRYPTION_KEY)

def encrypt_password(password: str) -> str:
    """Encrypt a password string using Fernet."""
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(token: str) -> str:
    """Decrypt a Fernet-encrypted password string."""
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        raise ValueError("Invalid encryption token or key.") 