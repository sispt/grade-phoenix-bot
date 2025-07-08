import sys
from sqlalchemy import create_engine, inspect, text
from storage.models import Base
from config import CONFIG

def migrate():
    database_url = CONFIG["DATABASE_URL"]
    engine = create_engine(database_url)
    insp = inspect(engine)
    with engine.connect() as conn:
        columns = [col['name'] for col in insp.get_columns('grades')]
        if 'user_id' in columns:
            print("[MIGRATION] Dropping existing user_id column from grades table...")
            conn.execute(text('ALTER TABLE grades DROP COLUMN user_id CASCADE'))
            print("[MIGRATION] user_id column dropped.")
        columns = [col['name'] for col in insp.get_columns('grades')]  # Refresh columns
        if 'user_id' not in columns:
            print("[MIGRATION] Adding user_id column to grades table...")
            conn.execute(text('ALTER TABLE grades ADD COLUMN user_id INTEGER'))
            print("[MIGRATION] Migrating user_id values from telegram_id...")
            conn.execute(text('UPDATE grades SET user_id = users.id FROM users WHERE grades.telegram_id = users.telegram_id'))
            print("[MIGRATION] Setting user_id column as NOT NULL...")
            conn.execute(text('ALTER TABLE grades ALTER COLUMN user_id SET NOT NULL'))
            print("[MIGRATION] Adding foreign key constraint to user_id...")
            conn.execute(text('ALTER TABLE grades ADD CONSTRAINT grades_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE'))
            print("[MIGRATION] user_id migration complete.")
        else:
            print("[MIGRATION] user_id column already exists in grades table. No migration needed.")
        if 'term_id' not in columns:
            print("[MIGRATION] Adding term_id column to grades table...")
            conn.execute(text('ALTER TABLE grades ADD COLUMN term_id INTEGER'))
            print("[MIGRATION] term_id column added.")

if __name__ == "__main__":
    migrate() 