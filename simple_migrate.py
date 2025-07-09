# simple_migrate.py
# Migration script to add 'do_trans' column to 'users' table

from storage.models import DatabaseManager
from config import CONFIG
from sqlalchemy import text

DB_URL = CONFIG["MYSQL_URL"]

def add_do_trans_column():
    db = DatabaseManager(DB_URL)
    engine = db.engine
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SHOW COLUMNS FROM users LIKE 'do_trans';
        """))
        if result.fetchone():
            print("Column 'do_trans' already exists.")
            return
        # Add the column
        print("Adding 'do_trans' column to 'users' table...")
        conn.execute(text("""
            ALTER TABLE users ADD COLUMN do_trans BOOLEAN NOT NULL DEFAULT 0;
        """))
        print("Column 'do_trans' added successfully.")

if __name__ == "__main__":
    add_do_trans_column()