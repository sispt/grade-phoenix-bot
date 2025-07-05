"""
Create Database Tables Script
Creates all database tables from scratch using SQLAlchemy models.
"""

import logging
from config import CONFIG
from storage.models import Base, DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("create_database")

def create_all_tables():
    """Create all database tables from scratch"""
    logger.info("🚀 Creating all database tables...")
    logger.info(f"🔧 Database URL: {CONFIG['DATABASE_URL']}")
    
    try:
        # Create database manager
        db_manager = DatabaseManager(CONFIG['DATABASE_URL'])
        
        # Create all tables
        success = db_manager.create_all_tables()
        
        if success:
            logger.info("✅ All database tables created successfully!")
            
            # Test connection
            if db_manager.test_connection():
                logger.info("✅ Database connection test successful!")
                return True
            else:
                logger.error("❌ Database connection test failed!")
                return False
        else:
            logger.error("❌ Failed to create database tables!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error creating database: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = create_all_tables()
    if success:
        print("\n✅ Database creation completed successfully!")
        print("📊 All tables created with proper schema:")
        print("   - users")
        print("   - grades") 
        print("   - terms")
        print("   - grade_history")
        print("   - credential_tests")
        print("\n🔄 Your database is now ready for the bot!")
    else:
        print("\n❌ Database creation failed!")
        print("🔧 Please check the logs above for details.")
        exit(1) 