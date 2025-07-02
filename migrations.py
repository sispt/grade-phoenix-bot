#!/usr/bin/env python3
"""
Database Migration & Password Security Script
This script is used by Railway deployment to run all migrations and password audits before starting the bot.
"""
import sys
import os
import logging
from sqlalchemy import text
from config import CONFIG
from storage.models import DatabaseManager, Base, User
from storage.postgresql_users import PostgreSQLUserStorage
from storage.users import UserStorage
from utils.security_enhancements import is_password_hashed, hash_password

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_status():
    """Check database connection and table status"""
    try:
        db_url = CONFIG.get("DATABASE_URL")
        if not db_url:
            logger.error("❌ DATABASE_URL not found in config")
            return False
        db_manager = DatabaseManager(db_url)
        if not db_manager.test_connection():
            logger.error("❌ Cannot connect to database")
            return False
        logger.info("✅ Database status check passed")
        return True
    except Exception as e:
        logger.error(f"❌ Database status check failed: {e}")
        return False

def migrate_schema():
    """Run database schema migrations (create tables, remove deprecated columns)"""
    try:
        db_url = CONFIG.get("DATABASE_URL")
        if not db_url:
            logger.error("❌ DATABASE_URL not found in config")
            return False
        db_manager = DatabaseManager(db_url)
        if not db_manager.test_connection():
            logger.error("❌ Cannot connect to database")
            return False
        logger.info("🔄 Running database migrations...")
        
        # Create tables if they don't exist (this is the most important part)
        try:
            Base.metadata.create_all(bind=db_manager.engine)
            logger.info("✅ Database tables created/verified successfully")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            return False
        
        # Try to remove deprecated columns (PostgreSQL only, skip on SQLite)
        if "postgresql" in db_url.lower():
            try:
                with db_manager.get_session() as session:
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
                logger.warning(f"⚠️ Could not check/remove encrypted_password column (PostgreSQL only): {e}")
                # Don't fail the migration for this - it's not critical
        else:
            logger.info("ℹ️ Skipping column removal (SQLite detected)")
        
        logger.info("✅ Database migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error running migrations: {e}", exc_info=True)
        return False

def audit_passwords():
    """Audit password storage for all users (PostgreSQL and JSON)"""
    logger.info("🔐 Starting Password Security Audit...")
    storage_type = CONFIG.get("STORAGE_TYPE", "postgresql").lower()
    success = True
    # PostgreSQL
    if storage_type in ("postgresql", "both"):
        db_url = CONFIG.get("DATABASE_URL")
        if db_url:
            db_manager = DatabaseManager(db_url)
            if db_manager.test_connection():
                with db_manager.get_session() as session:
                    users = session.query(User).all()
                    total = len(users)
                    hashed = 0
                    plain = 0
                    for user in users:
                        password = str(user.password) if user.password is not None else None
                        if not password:
                            continue
                        if is_password_hashed(password):
                            hashed += 1
                        else:
                            plain += 1
                            logger.warning(f"🚨 User {user.telegram_id} has PLAIN TEXT password: {password[:10]}... (must re-login)")
                    logger.info(f"📊 PostgreSQL: {hashed}/{total} hashed, {plain} plain text.")
                    if plain > 0:
                        logger.error("❌ Found plain text passwords in PostgreSQL!")
                        success = False
            else:
                logger.warning("⚠️ Cannot connect to PostgreSQL for password audit.")
    # JSON
    if storage_type in ("json", "both"):
        user_storage = UserStorage()
        users = user_storage.get_all_users()
        total = len(users)
        hashed = 0
        plain = 0
        for user in users:
            password = user.get("password")
            if not password:
                continue
            if is_password_hashed(password):
                hashed += 1
            else:
                plain += 1
                logger.warning(f"🚨 User {user.get('telegram_id')} has PLAIN TEXT password: {password[:10]}... (must re-login)")
        logger.info(f"📊 JSON: {hashed}/{total} hashed, {plain} plain text.")
        if plain > 0:
            logger.error("❌ Found plain text passwords in JSON storage!")
            success = False
    if success:
        logger.info("✅ All passwords are properly hashed!")
    else:
        logger.error("🚨 CRITICAL: Some users must re-login to secure their passwords!")
    return success

def main():
    logger.info("🔄 Starting database migrations and password audit...")
    
    # Check database status
    if not check_database_status():
        logger.error("❌ Database connection failed")
        sys.exit(1)
    
    # Run migrations (don't fail if column removal fails)
    migrate_success = migrate_schema()
    if not migrate_success:
        logger.error("❌ Critical database migrations failed")
        sys.exit(1)
    
    # Run password audit (don't fail if audit finds issues)
    audit_success = audit_passwords()
    if not audit_success:
        logger.warning("⚠️ Password audit found issues, but continuing...")
    
    logger.info("✅ All migrations and password audits completed successfully!")
    sys.exit(0)

if __name__ == "__main__":
    main() 