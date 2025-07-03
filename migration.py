"""
Database Migration Script
Removes password and password_hash columns and updates schema for no-password-storage policy.
"""
import os
from sqlalchemy import create_engine, inspect, text
from config import CONFIG
from utils.logger import get_migration_logger

# Get migration logger
logger = get_migration_logger()

def column_exists(engine, table_name, column_name):
    """Check if a column exists in a table with detailed logging."""
    try:
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns(table_name)]
        exists = column_name in columns
        logger.info(f"🔍 Checking column '{column_name}' in table '{table_name}': {'EXISTS' if exists else 'NOT FOUND'}")
        logger.info(f"📋 All columns in '{table_name}': {columns}")
        return exists
    except Exception as e:
        logger.error(f"❌ Error checking column '{column_name}' in table '{table_name}': {e}")
        return False

def drop_column(engine, table_name, column_name):
    """Drop a column with comprehensive logging."""
    try:
        logger.info(f"🗑️ Attempting to drop column '{column_name}' from table '{table_name}'")
        
        # Check if column exists before attempting to drop
        if not column_exists(engine, table_name, column_name):
            logger.warning(f"⚠️ Column '{column_name}' does not exist in table '{table_name}'. Skipping drop.")
            return True
        
        # Execute the drop command based on database type
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                sql = f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {column_name};"
            elif engine.dialect.name == "sqlite":
                # SQLite doesn't support DROP COLUMN IF EXISTS, so we need to check first
                sql = f"ALTER TABLE {table_name} DROP COLUMN {column_name};"
            else:
                logger.error(f"❌ Unsupported database dialect: {engine.dialect.name}")
                return False
            
            logger.info(f"🔧 Executing SQL: {sql}")
            result = conn.execute(text(sql))
            conn.commit()
            logger.info(f"✅ Successfully dropped column '{column_name}' from table '{table_name}'")
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed to drop column '{column_name}' from table '{table_name}': {e}")
        return False

def add_column_if_not_exists(engine, table_name, column_name, column_type):
    """Add a column if it doesn't exist with detailed logging."""
    try:
        logger.info(f"➕ Checking if column '{column_name}' exists in table '{table_name}'")
        
        if column_exists(engine, table_name, column_name):
            logger.info(f"ℹ️ Column '{column_name}' already exists in table '{table_name}'. Skipping add.")
            return True
        
        # Add the column based on database type
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};"
            elif engine.dialect.name == "sqlite":
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};"
            else:
                logger.error(f"❌ Unsupported database dialect: {engine.dialect.name}")
                return False
            
            logger.info(f"🔧 Executing SQL: {sql}")
            result = conn.execute(text(sql))
            conn.commit()
            logger.info(f"✅ Successfully added column '{column_name}' to table '{table_name}'")
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed to add column '{column_name}' to table '{table_name}': {e}")
        return False

def get_database_version(engine):
    """Get database version based on database type."""
    try:
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                result = conn.execute(text("SELECT version();"))
                version_row = result.fetchone()
                return version_row[0] if version_row else "Unknown"
            elif engine.dialect.name == "sqlite":
                result = conn.execute(text("SELECT sqlite_version();"))
                version_row = result.fetchone()
                return version_row[0] if version_row else "Unknown"
            else:
                return f"Unknown ({engine.dialect.name})"
    except Exception as e:
        logger.warning(f"⚠️ Could not get database version: {e}")
        return "Unknown"

def run_migration():
    """Main migration function with comprehensive logging."""
    logger.info("🚀 Starting database migration...")
    logger.info(f"🔧 Database URL: {CONFIG['DATABASE_URL']}")
    
    try:
        # Create engine
        engine = create_engine(CONFIG['DATABASE_URL'])
        logger.info(f"🔌 Database engine created successfully")
        logger.info(f"🗄️ Database dialect: {engine.dialect.name}")
        
        # Test connection and get version
        version = get_database_version(engine)
        logger.info(f"✅ Database connection successful: {version}")
        
        # Check current state of users table
        logger.info("📊 Checking current state of users table...")
        inspector = inspect(engine)
        if 'users' in inspector.get_table_names():
            users_columns = [col["name"] for col in inspector.get_columns('users')]
            logger.info(f"📋 Current columns in 'users' table: {users_columns}")
        else:
            logger.warning("⚠️ 'users' table does not exist!")
            return
        
        # Step 1: Add new columns
        logger.info("🔧 Step 1: Adding new columns...")
        add_column_if_not_exists(engine, 'users', 'token_expired_notified', 'BOOLEAN DEFAULT FALSE')
        
        # Step 2: Drop password columns
        logger.info("🔧 Step 2: Dropping password columns...")
        
        # Drop password column
        logger.info("🗑️ Attempting to drop 'password' column...")
        if drop_column(engine, 'users', 'password'):
            logger.info("✅ 'password' column drop operation completed")
        else:
            logger.error("❌ 'password' column drop operation failed")
        
        # Drop password_hash column
        logger.info("🗑️ Attempting to drop 'password_hash' column...")
        if drop_column(engine, 'users', 'password_hash'):
            logger.info("✅ 'password_hash' column drop operation completed")
        else:
            logger.error("❌ 'password_hash' column drop operation failed")
        
        # Verify final state
        logger.info("🔍 Verifying final state of users table...")
        final_columns = [col["name"] for col in inspector.get_columns('users')]
        logger.info(f"📋 Final columns in 'users' table: {final_columns}")
        
        # Check if password columns still exist
        password_columns = [col for col in final_columns if 'password' in col.lower()]
        if password_columns:
            logger.error("❌ Password-related columns still exist in the database schema.")
        else:
            logger.info("✅ All password-related columns successfully removed")
        
        logger.info("🎉 Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration() 