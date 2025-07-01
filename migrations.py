"""
Database Table Creation Script (using SQLAlchemy models)

This script will create all tables defined in storage/models.py.
"""
from storage.models import Base, DatabaseManager
from config import CONFIG
import os
import psycopg2

# Get the database URL from environment or config
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    from config import CONFIG
    DATABASE_URL = CONFIG.get('DATABASE_URL')

ALTER_DROP = """
ALTER TABLE grades DROP CONSTRAINT IF EXISTS grades_telegram_id_fkey;
"""
ALTER_ADD = """
ALTER TABLE grades
ADD CONSTRAINT grades_telegram_id_fkey
FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE;
"""

def run_migration():
    print("Connecting to DB...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        print("Dropping old foreign key constraint if exists...")
        cur.execute(ALTER_DROP)
        print("Adding new foreign key constraint with ON DELETE CASCADE...")
        cur.execute(ALTER_ADD)
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_migration() 