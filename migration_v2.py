#!/usr/bin/env python3
import logging
from storage.models import DatabaseManager

from config import CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMigrationV2:
    def remove_password_columns(self):
        """Remove password storage columns from the User table if they exist"""
        from sqlalchemy import text
        logger.info("🗑️ Removing password storage columns from users table if they exist...")
        db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
        with db_manager.get_session() as session:
            try:
                session.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS encrypted_password"))
                logger.info("✅ Removed encrypted_password column if it existed.")
            except Exception as e:
                logger.warning(f"⚠️ Could not remove encrypted_password column: {e}")
            try:
                session.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS password_stored"))
                logger.info("✅ Removed password_stored column if it existed.")
            except Exception as e:
                logger.warning(f"⚠️ Could not remove password_stored column: {e}")

    def run_migration(self):
        """Run complete migration process"""
        try:
            logger.info("🚀 Starting V2 Migration Process...")
            # Remove password columns if they exist
            self.remove_password_columns()
            logger.info("🎉 Migration completed successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}", exc_info=True)
            return False


def main():
    """Main migration function"""
    try:
        migration = DataMigrationV2()
        success = migration.run_migration()
        
        if success:
            print("✅ Migration completed successfully!")
        else:
            print("❌ Migration failed. Check the logs for details.")
            return 1
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 