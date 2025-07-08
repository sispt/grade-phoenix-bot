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
        # Migrate existing grades to grade_history if history is empty
        result = conn.execute(text('SELECT COUNT(*) FROM grade_history'))
        history_count = result.scalar() if hasattr(result, 'scalar') else list(result)[0][0]
        if history_count == 0:
            print("[MIGRATION] Migrating existing grades to grade_history...")
            conn.execute(text('''
                INSERT INTO grade_history (user_id, grade_id, previous_total_grade, previous_numeric_grade, previous_status, change_type, changed_at)
                SELECT user_id, id, total_grade_value, numeric_grade, grade_status, 'Created', NOW()
                FROM grades
            '''))
            print("[MIGRATION] Migration to grade_history complete.")
        else:
            print("[MIGRATION] grade_history already contains data. No migration needed.")

if __name__ == "__main__":
    migrate() 