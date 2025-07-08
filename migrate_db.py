import sys
from sqlalchemy import create_engine, inspect, text
from storage.models import Base
from config import CONFIG

def migrate():
    database_url = CONFIG["DATABASE_URL"]
    engine = create_engine(database_url)
    insp = inspect(engine)
    with engine.connect() as conn:
        # Drop the old grades table if it exists
        print("[MIGRATION] Dropping old grades table if it exists...")
        conn.execute(text('DROP TABLE IF EXISTS grades CASCADE'))
        print("[MIGRATION] Old grades table dropped.")
        # Recreate the grades table with the new schema
        print("[MIGRATION] Creating new grades table with telegram_id as FK...")
        Base.metadata.create_all(engine, tables=[Base.metadata.tables['grades']])
        print("[MIGRATION] New grades table created.")

if __name__ == "__main__":
    migrate() 