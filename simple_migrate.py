import os
import sqlalchemy
from sqlalchemy import create_engine, text
from config import CONFIG

def add_column_if_missing(conn, table, column, coltype):
    result = conn.execute(text(f"""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE table_name = '{table}' AND column_name = '{column}';
    """))
    exists = result.scalar() > 0
    if exists:
        print(f"Column '{column}' already exists in '{table}' table.")
        return
    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {coltype};"))
    print(f"Column '{column}' added to '{table}' table.")

def migrate_users_table():
    db_url = CONFIG["MYSQL_URL"]
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=300, connect_args={"charset": "utf8mb4"})
    with engine.connect() as conn:
        add_column_if_missing(conn, 'users', 'encrypted_password', 'VARCHAR(255) NULL')
        add_column_if_missing(conn, 'users', 'is_active', 'BOOLEAN DEFAULT TRUE')
        add_column_if_missing(conn, 'users', 'session_expired_notified', 'BOOLEAN DEFAULT FALSE')
        add_column_if_missing(conn, 'users', 'password_stored', 'BOOLEAN DEFAULT FALSE')
        add_column_if_missing(conn, 'users', 'password_consent_given', 'BOOLEAN DEFAULT FALSE')

if __name__ == "__main__":
    migrate_users_table()