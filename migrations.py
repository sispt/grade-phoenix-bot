import os
from sqlalchemy import create_engine, text
from config import CONFIG

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

def main():
    database_url = CONFIG["DATABASE_URL"]
    engine = create_engine(database_url)
    run_sql_file(engine, SQL_FILE)

if __name__ == "__main__":
    main() 