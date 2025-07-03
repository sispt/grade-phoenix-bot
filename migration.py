"""
Database Migration Script
Removes password and password_hash columns and updates schema for no-password-storage policy.
"""
import os
import logging
from sqlalchemy import create_engine, inspect, text
from config import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def column_exists(engine, table_name, column_name):
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns

def drop_column(engine, table_name, column_name):
    try:
        if engine.dialect.name != "postgresql":
            logger.error(f"❌ This migration only supports PostgreSQL. Detected: {engine.dialect.name}")
            return
        with engine.connect() as conn:
            logger.info(f"Attempting to drop column '{column_name}' from '{table_name}'...")
            conn.execute(text(f'ALTER TABLE {table_name} DROP COLUMN IF EXISTS {column_name}'))
            conn.commit()
            logger.info(f"✅ Successfully dropped column '{column_name}' from '{table_name}' (if it existed).")
    except Exception as e:
        logger.error(f"❌ Error dropping column '{column_name}' from '{table_name}': {e}")
        raise

def add_token_expired_notified_column(engine):
    try:
        if engine.dialect.name != "postgresql":
            logger.error(f"❌ This migration only supports PostgreSQL. Detected: {engine.dialect.name}")
            return
        if not column_exists(engine, "users", "token_expired_notified"):
            with engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN token_expired_notified BOOLEAN DEFAULT FALSE;"
                ))
                conn.commit()
                logger.info("✅ Added token_expired_notified column to users table.")
        else:
            logger.info("ℹ️ token_expired_notified column already exists in users table.")
    except Exception as e:
        logger.error(f"❌ Error adding token_expired_notified column: {e}")
        raise

def main():
    logger.info("🚀 Starting database migration...")
    db_url = CONFIG.get("DATABASE_URL")
    if not db_url:
        logger.error("❌ DATABASE_URL not found in config.")
        return

    try:
        engine = create_engine(db_url)
        inspector = inspect(engine)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful.")

        if engine.dialect.name != "postgresql":
            logger.error(f"❌ This migration only supports PostgreSQL. Detected: {engine.dialect.name}")
            return

        if "users" in inspector.get_table_names():
            add_token_expired_notified_column(engine)
            if column_exists(engine, "users", "password"):
                drop_column(engine, "users", "password")
            else:
                logger.info("ℹ️ 'password' column not found in 'users' table (already removed).")
        else:
            logger.warning("⚠️ 'users' table not found. Skipping column additions/removals.")

        if "credential_tests" in inspector.get_table_names():
            if column_exists(engine, "credential_tests", "password_hash"):
                drop_column(engine, "credential_tests", "password_hash")
            else:
                logger.info("ℹ️ 'password_hash' column not found in 'credential_tests' table (already removed or never existed).")
        else:
            logger.info("ℹ️ 'credential_tests' table not found.")

        logger.info("✅ Database migration completed successfully!")

    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        raise

if __name__ == "__main__":
    main() 