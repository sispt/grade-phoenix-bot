#!/usr/bin/env python3
"""
🗄️ Database Creation Script V2
Creates all database tables for the new V2 storage systems
"""

import logging
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError

from config import CONFIG
from storage.user_storage_v2 import Base as UserBase
from storage.grade_storage_v2 import Base as GradeBase

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_database_tables():
    """Create all database tables for V2 storage systems"""
    try:
        logger.info("🗄️ Creating database tables for V2 storage systems...")
        
        # Create engine
        engine = create_engine(CONFIG["DATABASE_URL"])
        
        # Test connection
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        
        # Get inspector to check existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"📋 Existing tables: {existing_tables}")
        
        # Create User tables (from user_storage_v2)
        logger.info("👥 Creating user tables...")
        UserBase.metadata.create_all(bind=engine)
        
        # Create Grade tables (from grade_storage_v2)
        logger.info("📊 Creating grade tables...")
        GradeBase.metadata.create_all(bind=engine)
        
        # Verify tables were created
        inspector = inspect(engine)
        new_tables = inspector.get_table_names()
        logger.info(f"📋 All tables after creation: {new_tables}")
        
        # Check specific tables
        expected_tables = ["users", "terms", "grades"]
        for table in expected_tables:
            if table in new_tables:
                columns = [col["name"] for col in inspector.get_columns(table)]
                logger.info(f"✅ Table '{table}' created with columns: {columns}")
            else:
                logger.error(f"❌ Table '{table}' was not created")
                return False
        
        logger.info("🎉 Database tables created successfully!")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}", exc_info=True)
        return False


def main():
    """Main function"""
    try:
        success = create_database_tables()
        
        if success:
            print("✅ Database tables created successfully!")
            print("🗄️ The V2 storage systems are ready to use.")
        else:
            print("❌ Failed to create database tables. Check the logs for details.")
            return 1
            
    except Exception as e:
        print(f"❌ Database creation error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 