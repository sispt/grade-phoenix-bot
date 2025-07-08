import os
from sqlalchemy import create_engine, text
from config import CONFIG
from storage.models import DatabaseManager

SQL_FILE = 'migrate_grades.sql'

def run_sql_file(engine, sql_file):
    print(f"[MIGRATION] Running migration file: {sql_file}")
    with open(sql_file, 'r') as f:
        sql_commands = f.read()
    conn = engine.raw_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute(sql_commands)
            conn.commit()
            print("[MIGRATION] Migration completed successfully.")
        except Exception as e:
            print(f"[MIGRATION] Error during migration: {e}")
            conn.rollback()
        finally:
            cursor.close()
    finally:
        conn.close()

if __name__ == "__main__":
    db_url = CONFIG.get('DATABASE_URL') or os.environ.get('DATABASE_URL')
    if not db_url:
        print("Please set the DATABASE_URL environment variable.")
    else:
        # Auto-migrate if requested
        if os.environ.get('AUTO_MIGRATE') == '1':
            print("[MIGRATION] AUTO_MIGRATE is set. Running create_all_tables...")
            DatabaseManager.create_all_tables_for_url(db_url)
        # Optionally run SQL file
        if os.path.exists(SQL_FILE):
            engine = create_engine(db_url)
            run_sql_file(engine, SQL_FILE) 