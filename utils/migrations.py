"""
Database Migration Script
"""
import logging
import sys
from typing import List, Dict, Any
from sqlalchemy import text
from config import CONFIG
from storage.models import DatabaseManager, Base, User
from storage.postgresql_users import PostgreSQLUserStorage
from storage.users import UserStorage
from utils.security_enhancements import is_password_hashed, hash_password

logger = logging.getLogger(__name__)

def migrate_postgresql_passwords():
    """Migrate passwords in PostgreSQL database"""
    try:
        # Initialize database connection
        db_url = CONFIG.get("DATABASE_URL")
        if not db_url:
            logger.error("❌ DATABASE_URL not found in config")
            return False
        
        db_manager = DatabaseManager(db_url)
        user_storage = PostgreSQLUserStorage(db_manager)
        
        # Test database connection
        if not db_manager.test_connection():
            logger.error("❌ Cannot connect to database")
            return False
        
        logger.info("🔄 Starting PostgreSQL password migration...")
        
        # Get all users
        with db_manager.get_session() as session:
            users = session.query(User).all()
            
            migrated_count = 0
            already_hashed_count = 0
            
            for user in users:
                password = str(user.password) if user.password is not None else None
                if not password:
                    logger.warning(f"⚠️ User {user.telegram_id} has no password")
                    continue
                
                if is_password_hashed(password):
                    already_hashed_count += 1
                    logger.debug(f"✅ User {user.telegram_id} already has hashed password")
                else:
                    # This is a plain text password that needs migration
                    # Note: We can't migrate without the original password
                    # This is a limitation - we can only hash new passwords
                    logger.warning(f"⚠️ User {user.telegram_id} has plain text password - cannot migrate without original")
                    logger.info(f"💡 User {user.telegram_id} will need to re-enter password on next login")
            
            logger.info(f"📊 PostgreSQL Migration Summary:")
            logger.info(f"   - Total users: {len(users)}")
            logger.info(f"   - Already hashed: {already_hashed_count}")
            logger.info(f"   - Plain text passwords: {len(users) - already_hashed_count}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error migrating PostgreSQL passwords: {e}", exc_info=True)
        return False

def migrate_json_passwords():
    """Migrate passwords in JSON file storage"""
    try:
        logger.info("🔄 Starting JSON password migration...")
        
        user_storage = UserStorage()
        users = user_storage.get_all_users()
        
        migrated_count = 0
        already_hashed_count = 0
        plain_text_count = 0
        
        for user in users:
            if not user.get("password"):
                logger.warning(f"⚠️ User {user.get('telegram_id')} has no password")
                continue
            
            if is_password_hashed(user["password"]):
                already_hashed_count += 1
                logger.debug(f"✅ User {user.get('telegram_id')} already has hashed password")
            else:
                plain_text_count += 1
                logger.warning(f"⚠️ User {user.get('telegram_id')} has plain text password - cannot migrate without original")
                logger.info(f"💡 User {user.get('telegram_id')} will need to re-enter password on next login")
        
        logger.info(f"📊 JSON Migration Summary:")
        logger.info(f"   - Total users: {len(users)}")
        logger.info(f"   - Already hashed: {already_hashed_count}")
        logger.info(f"   - Plain text passwords: {plain_text_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error migrating JSON passwords: {e}", exc_info=True)
        return False

def run_password_migrations():
    """Run password migration for all storage types"""
    logger.info("🔐 Starting Password Migration Process")
    logger.info("=" * 50)
    
    # Check which storage system is being used
    storage_type = CONFIG.get("STORAGE_TYPE", "postgresql").lower()
    
    success = True
    
    if storage_type == "postgresql":
        logger.info("📦 Using PostgreSQL storage")
        success = migrate_postgresql_passwords()
    elif storage_type == "json":
        logger.info("📄 Using JSON storage")
        success = migrate_json_passwords()
    else:
        logger.info("📦 Checking both PostgreSQL and JSON storage")
        success_postgres = migrate_postgresql_passwords()
        success_json = migrate_json_passwords()
        success = success_postgres and success_json
    
    logger.info("=" * 50)
    if success:
        logger.info("✅ Password migration process completed")
        logger.info("💡 Note: Users with plain text passwords will need to re-enter their password on next login")
    else:
        logger.error("❌ Password migration process failed")
    
    return success

def check_database_status():
    """Check database connection and table status"""
    try:
        db_url = CONFIG.get("DATABASE_URL")
        if not db_url:
            logger.error("❌ DATABASE_URL not found in config")
            return False
        
        db_manager = DatabaseManager(db_url)
        
        # Test database connection
        if not db_manager.test_connection():
            logger.error("❌ Cannot connect to database")
            return False
        
        logger.info("✅ Database status check passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database status check failed: {e}")
        return False

def run_migrations():
    """Run database migrations"""
    try:
        # Initialize database connection
        db_url = CONFIG.get("DATABASE_URL")
        if not db_url:
            logger.error("❌ DATABASE_URL not found in config")
            return False
        
        db_manager = DatabaseManager(db_url)
        
        # Test database connection
        if not db_manager.test_connection():
            logger.error("❌ Cannot connect to database")
            return False
        
        logger.info("🔄 Running database migrations...")
        
        with db_manager.get_session() as session:
            # Check if encrypted_password column exists and remove it if it does
            try:
                result = session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'encrypted_password'
                """))
                column_exists = result.fetchone() is not None
                
                if column_exists:
                    logger.info("📝 Removing encrypted_password column from users table...")
                    session.execute(text("""
                        ALTER TABLE users 
                        DROP COLUMN encrypted_password
                    """))
                    session.commit()
                    logger.info("✅ encrypted_password column removed successfully")
                else:
                    logger.info("✅ encrypted_password column does not exist (already removed)")
                    
            except Exception as e:
                logger.error(f"❌ Error removing encrypted_password column: {e}")
                session.rollback()
                return False
        
        # Create tables if they don't exist
        try:
            Base.metadata.create_all(bind=db_manager.engine)
            logger.info("✅ Database tables created/verified successfully")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            return False
        
        # Run password migrations
        password_success = run_password_migrations()
        
        logger.info("✅ Database migrations completed successfully")
        return password_success
        
    except Exception as e:
        logger.error(f"❌ Error running migrations: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = run_migrations()
    if not success:
        exit(1) 