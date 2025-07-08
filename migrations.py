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

def main():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print('Please set the DATABASE_URL environment variable.')
        return
    print(f'Creating all tables in: {db_url}')
    DatabaseManager.create_all_tables_for_url(db_url)
    print('✅ All tables created! You can now use your new database.')

if __name__ == '__main__':
    main() 