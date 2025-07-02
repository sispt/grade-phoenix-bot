#!/usr/bin/env python3
"""
Hash Existing Passwords Script
Read plain text passwords from database, hash them, and replace the plain text with the hash
"""
import logging
import sys
from config import CONFIG
from storage.models import DatabaseManager, User
from storage.users import UserStorage
from utils.security_enhancements import is_password_hashed, hash_password

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def hash_postgresql_passwords():
    """Hash plain text passwords in PostgreSQL database"""
    try:
        db_url = CONFIG.get("DATABASE_URL")
        if not db_url:
            logger.error("❌ DATABASE_URL not found")
            return False
        
        db_manager = DatabaseManager(db_url)
        if not db_manager.test_connection():
            logger.error("❌ Cannot connect to database")
            return False
        
        logger.info("🔄 Hashing plain text passwords in PostgreSQL...")
        
        with db_manager.get_session() as session:
            users = session.query(User).all()
            hashed_count = 0
            
            for user in users:
                password = str(user.password) if user.password is not None else None
                if not password:
                    continue
                
                if not is_password_hashed(password):
                    # Hash the plain text password
                    hashed_password = hash_password(password)
                    user.password = hashed_password
                    hashed_count += 1
                    logger.info(f"🔐 Hashed password for user {user.telegram_id}: {password[:10]}... -> {hashed_password[:20]}...")
                else:
                    logger.debug(f"✅ User {user.telegram_id} already has hashed password")
            
            session.commit()
            logger.info(f"✅ Successfully hashed {hashed_count} passwords in PostgreSQL")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error hashing passwords: {e}", exc_info=True)
        return False

def hash_json_passwords():
    """Hash plain text passwords in JSON storage"""
    try:
        user_storage = UserStorage()
        users = user_storage.get_all_users()
        hashed_count = 0
        
        for user in users:
            password = user.get("password")
            if not password:
                continue
            
            if not is_password_hashed(password):
                # Hash the plain text password
                hashed_password = hash_password(password)
                user["password"] = hashed_password
                hashed_count += 1
                logger.info(f"🔐 Hashed password for user {user.get('telegram_id')}: {password[:10]}... -> {hashed_password[:20]}...")
            else:
                logger.debug(f"✅ User {user.get('telegram_id')} already has hashed password")
        
        user_storage._save_users()
        logger.info(f"✅ Successfully hashed {hashed_count} passwords in JSON storage")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error hashing passwords: {e}", exc_info=True)
        return False

def main():
    logger.info("🔐 Hash Existing Passwords Script")
    logger.info("=" * 50)
    
    storage_type = CONFIG.get("STORAGE_TYPE", "postgresql").lower()
    
    if storage_type == "postgresql":
        hash_postgresql_passwords()
    elif storage_type == "json":
        hash_json_passwords()
    else:
        hash_postgresql_passwords()
        hash_json_passwords()
    
    logger.info("✅ All plain text passwords have been hashed!")
    logger.info("🔐 Your database is now fully secure!")

if __name__ == "__main__":
    main() 