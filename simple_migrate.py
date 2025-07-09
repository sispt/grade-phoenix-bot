#!/usr/bin/env python3
"""
Migration Script Template
------------------------
This script is a template for future database migrations.
Add your migration logic below. Use SQLAlchemy for cross-DB operations.
"""

import os
import sys
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker

# Example usage:
# 1. Set up environment variables for your source/target DBs
# 2. Add your migration logic below

def main():
    import sqlalchemy
    from sqlalchemy import inspect, text
    db_url = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL")
    if not db_url:
        print("DATABASE_URL or MYSQL_URL environment variable not set.")
        sys.exit(1)
    engine = create_engine(db_url)
    with engine.connect() as conn:
        inspector = inspect(conn)
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'session_expired_notified' in columns:
            print("Column 'session_expired_notified' already exists in 'users' table.")
        else:
            # Add the column
            print("Adding 'session_expired_notified' column to 'users' table...")
            try:
                conn.execute(text("""
                    ALTER TABLE users ADD COLUMN session_expired_notified BOOLEAN NOT NULL DEFAULT FALSE
                """))
                print("Column added successfully.")
            except Exception as e:
                print(f"Failed to add column: {e}")

if __name__ == "__main__":
    main() 