"""
Database Migration Script
Removes password and password_hash columns and updates schema for no-password-storage policy.
Only runs if DATABASE_MIGRATE env var is true.
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
        with engine.connect() as conn:
            logger.info(f"Attempting to drop column '{column_name}' from '{table_name}'...")
            conn.execute(text(f'ALTER TABLE {table_name} DROP COLUMN IF EXISTS {column_name}'))
            logger.info(f"Dropped column '{column_name}' from '{table_name}' (if it existed).")
    except Exception as e:
        logger.error(f"Error dropping column '{column_name}' from '{table_name}': {e}")

def add_token_expired_notified_column():
    db_url = CONFIG["DATABASE_URL"]
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='users' AND column_name='token_expired_notified';
        """))
        if not result.fetchone():
            # Add the column
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN token_expired_notified BOOLEAN DEFAULT FALSE;
            """))
            print("Added token_expired_notified column to users table.")
        else:
            print("token_expired_notified column already exists.")

def main():
    if os.getenv("DATABASE_MIGRATE", "false").lower() != "true":
        logger.info("DATABASE_MIGRATE is not set to true. Skipping migration.")
        return

    db_url = CONFIG.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not found in config.")
        return

    engine = create_engine(db_url)
    inspector = inspect(engine)

    # Remove password column from users table
    if "users" in inspector.get_table_names():
        if column_exists(engine, "users", "password"):
            drop_column(engine, "users", "password")
        else:
            logger.info("'password' column not found in 'users' table.")
    else:
        logger.info("'users' table not found.")

    # Remove legacy password_hash column from credential_tests table if present
    if "credential_tests" in inspector.get_table_names():
        if column_exists(engine, "credential_tests", "password_hash"):
            drop_column(engine, "credential_tests", "password_hash")
            logger.info("'password_hash' column dropped from 'credential_tests' table.")
        else:
            logger.info("'password_hash' column not found in 'credential_tests' table (already removed or never existed).")
    else:
        logger.info("'credential_tests' table not found.")

    logger.info("Database migration completed.")

if __name__ == "__main__":
    if os.getenv("DATABASE_MIGRATE", "false").lower() == "true":
        add_token_expired_notified_column()
    else:
        main() 