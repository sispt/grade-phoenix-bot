"""
Database Table Creation Script (using SQLAlchemy models)

This script will create all tables defined in storage/models.py.
"""
from storage.models import Base, DatabaseManager
from config import CONFIG

if __name__ == "__main__":
    db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
    Base.metadata.create_all(bind=db_manager.engine)
    print("✅ All tables created!") 