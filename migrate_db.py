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
        if 'user_id' not in columns:
            print("[MIGRATION] Adding user_id column to grades table...")
            conn.execute(text('ALTER TABLE grades ADD COLUMN user_id INTEGER'))
            print("[MIGRATION] Migrating user_id values from telegram_id...")
            conn.execute(text('UPDATE grades SET user_id = (SELECT id FROM users WHERE users.telegram_id = grades.telegram_id)'))
            conn.execute(text('ALTER TABLE grades ALTER COLUMN user_id SET NOT NULL'))
            print("[MIGRATION] Adding foreign key constraint on user_id...")
            conn.execute(text('ALTER TABLE grades ADD CONSTRAINT fk_grades_user_id FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE'))
            print("[MIGRATION] Migration complete.")
        else:
            print("[MIGRATION] user_id column already exists in grades table. No migration needed.")

if __name__ == "__main__":
    migrate() 