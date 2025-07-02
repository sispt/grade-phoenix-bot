#!/usr/bin/env python3
"""
Database Migration Script - Root Level Entry Point
This file is used by Railway deployment to run migrations before starting the bot
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.migrations import run_migrations, run_password_migrations, check_database_status
    
    def main():
        """Main migration function"""
        print("🔄 Starting database migrations...")
        
        # Check database status first
        if not check_database_status():
            print("❌ Database connection failed")
            return False
        
        # Run database migrations
        if not run_migrations():
            print("❌ Database migrations failed")
            return False
        
        # Run password migrations
        if not run_password_migrations():
            print("❌ Password migrations failed")
            return False
        
        print("✅ All migrations completed successfully")
        return True
    
    if __name__ == "__main__":
        success = main()
        sys.exit(0 if success else 1)
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all dependencies are installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Migration error: {e}")
    sys.exit(1) 