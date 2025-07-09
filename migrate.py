#!/usr/bin/env python3
"""
Simple migration script for Railway predeploy
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

def run_migration():
    """Run Alembic migration"""
    try:
        # Import and run Alembic
        from alembic.config import Config
        from alembic import command
        
        # Create Alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Set the database URL
        database_url = os.getenv("MYSQL_URL")
        if database_url:
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        print("🗄️ Running database migration...")
        command.upgrade(alembic_cfg, "head")
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration() 