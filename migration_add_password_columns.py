#!/usr/bin/env python3
"""
Migration script to add password storage columns to the User table
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage.models import DatabaseManager, Base
from sqlalchemy import Column, String, Boolean, text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_password_columns():
    """Add password storage columns to the User table"""
    
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "sqlite:///data/bot.db")
    
    logger.info("🚀 Starting password columns migration...")
    logger.info(f"📊 Database URL: {database_url}")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(database_url)
        
        # Test connection
        if not db_manager.test_connection():
            logger.error("❌ Database connection failed")
            return False
        
        # Check if columns already exist
        with db_manager.get_session() as session:
            # Try to query the columns to see if they exist
            try:
                result = session.execute(text("""
                    SELECT encrypted_password, password_stored 
                    FROM users 
                    LIMIT 1
                """))
                logger.info("✅ Password columns already exist")
                return True
            except Exception as e:
                if "no such column" in str(e).lower():
                    logger.info("📝 Password columns do not exist, adding them...")
                else:
                    logger.error(f"❌ Error checking columns: {e}")
                    return False
        
        # Add the columns
        with db_manager.get_session() as session:
            # Add encrypted_password column
            session.execute(text("""
                ALTER TABLE users 
                ADD COLUMN encrypted_password VARCHAR(500)
            """))
            
            # Add password_stored column
            session.execute(text("""
                ALTER TABLE users 
                ADD COLUMN password_stored BOOLEAN DEFAULT FALSE NOT NULL
            """))
            
            logger.info("✅ Password columns added successfully")
        
        # Verify the columns were added
        with db_manager.get_session() as session:
            result = session.execute(text("""
                SELECT encrypted_password, password_stored 
                FROM users 
                LIMIT 1
            """))
            logger.info("✅ Password columns verified successfully")
        
        logger.info("🎉 Password columns migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = migrate_password_columns()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1) 