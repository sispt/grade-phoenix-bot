#!/usr/bin/env python3
"""
🔄 Migration Script V2 - Preserve Existing Data
Migrates data from old storage systems to new V2 tables
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import old storage systems
from storage.user_storage import UserStorage, PostgreSQLUserStorage
from storage.grade_storage import GradeStorage, PostgreSQLGradeStorage
from storage.models import DatabaseManager

# Import new storage systems
from storage.user_storage_v2 import UserStorageV2
from storage.grade_storage_v2 import GradeStorageV2

from config import CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMigrationV2:
    """Migrate data from old storage to new V2 storage"""
    
    def __init__(self):
        self.old_user_storage = None
        self.old_grade_storage = None
        self.new_user_storage = None
        self.new_grade_storage = None
        
    def initialize_storage_systems(self):
        """Initialize both old and new storage systems"""
        try:
            logger.info("🔄 Initializing storage systems for migration...")
            
            # Initialize new V2 storage
            self.new_user_storage = UserStorageV2(CONFIG["DATABASE_URL"])
            self.new_grade_storage = GradeStorageV2(CONFIG["DATABASE_URL"])
            logger.info("✅ New V2 storage systems initialized")
            
            # Initialize old storage systems
            if CONFIG["DATABASE_URL"].startswith("postgresql"):
                # Old PostgreSQL storage
                old_db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
                self.old_user_storage = PostgreSQLUserStorage(old_db_manager)
                self.old_grade_storage = PostgreSQLGradeStorage(old_db_manager)
                logger.info("✅ Old PostgreSQL storage systems initialized")
            else:
                # Old file-based storage
                self.old_user_storage = UserStorage()
                self.old_grade_storage = GradeStorage()
                logger.info("✅ Old file-based storage systems initialized")
                
        except Exception as e:
            logger.error(f"❌ Error initializing storage systems: {e}", exc_info=True)
            raise
    
    def migrate_users(self) -> int:
        """Migrate users from old storage to new V2 storage"""
        try:
            logger.info("👥 Starting user migration...")
            
            # Get all users from old storage
            old_users = []
            if self.old_user_storage and hasattr(self.old_user_storage, 'get_all_users'):
                old_users = self.old_user_storage.get_all_users()
            else:
                # For file-based storage, read the JSON file directly
                try:
                    if os.path.exists("data/users.json"):
                        with open("data/users.json", "r", encoding="utf-8") as f:
                            users_data = json.load(f)
                            for telegram_id, user_data in users_data.items():
                                user_data["telegram_id"] = int(telegram_id)
                                old_users.append(user_data)
                except Exception as e:
                    logger.warning(f"⚠️ Could not read file-based users: {e}")
            
            logger.info(f"📊 Found {len(old_users)} users to migrate")
            
            migrated_count = 0
            for user_data in old_users:
                try:
                    telegram_id = user_data.get("telegram_id")
                    username = user_data.get("username", "")
                    token = user_data.get("token", "")
                    
                    if not telegram_id:
                        logger.warning(f"⚠️ Skipping user with no telegram_id: {user_data}")
                        continue
                    
                    # Prepare user data for new storage
                    new_user_data = {
                        "username": username,
                        "fullname": user_data.get("fullname", ""),
                        "firstname": user_data.get("firstname", ""),
                        "lastname": user_data.get("lastname", ""),
                        "email": user_data.get("email", "")
                    }
                    
                    # Save to new storage
                    if self.new_user_storage:
                        success = self.new_user_storage.save_user(
                            telegram_id, username, token, new_user_data
                        )
                        
                        if success:
                            migrated_count += 1
                            logger.info(f"✅ Migrated user: {username} (ID: {telegram_id})")
                        else:
                            logger.error(f"❌ Failed to migrate user: {username} (ID: {telegram_id})")
                        
                except Exception as e:
                    logger.error(f"❌ Error migrating user {user_data}: {e}")
            
            logger.info(f"🎉 User migration completed: {migrated_count}/{len(old_users)} users migrated")
            return migrated_count
            
        except Exception as e:
            logger.error(f"❌ Error in user migration: {e}", exc_info=True)
            return 0
    
    def migrate_grades(self) -> int:
        """Migrate grades from old storage to new V2 storage"""
        try:
            logger.info("📊 Starting grade migration...")
            
            # Get all users from new storage to migrate their grades
            if not self.new_user_storage:
                logger.error("❌ New user storage not initialized")
                return 0
                
            new_users = self.new_user_storage.get_all_users()
            logger.info(f"📊 Found {len(new_users)} users to migrate grades for")
            
            total_migrated = 0
            
            for user_data in new_users:
                try:
                    telegram_id = user_data.get("telegram_id")
                    if not telegram_id:
                        continue
                    
                    # Get grades from old storage
                    old_grades = []
                    
                    if self.old_grade_storage and hasattr(self.old_grade_storage, 'get_grades'):
                        old_grades = self.old_grade_storage.get_grades(telegram_id)
                    else:
                        # For file-based storage, try to read grades file
                        try:
                            grades_file = f"data/grades_{telegram_id}.json"
                            if os.path.exists(grades_file):
                                with open(grades_file, "r", encoding="utf-8") as f:
                                    grades_data = json.load(f)
                                    old_grades = grades_data.get("grades", [])
                        except Exception as e:
                            logger.warning(f"⚠️ Could not read grades for user {telegram_id}: {e}")
                    
                    if old_grades:
                        # Transform grades to new format
                        new_grades = []
                        for grade in old_grades:
                            new_grade = {
                                "name": grade.get("name", ""),
                                "code": grade.get("code", ""),
                                "ects": grade.get("ects", ""),
                                "coursework": grade.get("coursework", ""),
                                "final_exam": grade.get("final_exam", ""),
                                "total": grade.get("total", ""),
                                "term_name": grade.get("term_name", "Previous Term"),
                                "term_id": grade.get("term_id", "unknown")
                            }
                            new_grades.append(new_grade)
                        
                        # Save to new storage
                        if self.new_grade_storage:
                            success = self.new_grade_storage.save_grades(telegram_id, new_grades)
                            
                            if success:
                                total_migrated += len(new_grades)
                                logger.info(f"✅ Migrated {len(new_grades)} grades for user {telegram_id}")
                            else:
                                logger.error(f"❌ Failed to migrate grades for user {telegram_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Error migrating grades for user {telegram_id}: {e}")
            
            logger.info(f"🎉 Grade migration completed: {total_migrated} grades migrated")
            return total_migrated
            
        except Exception as e:
            logger.error(f"❌ Error in grade migration: {e}", exc_info=True)
            return 0
    
    def create_backup(self):
        """Create backup of old data before migration"""
        try:
            logger.info("💾 Creating backup of old data...")
            
            backup_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "users": [],
                "grades": {}
            }
            
            # Backup users
            if self.old_user_storage and hasattr(self.old_user_storage, 'get_all_users'):
                backup_data["users"] = self.old_user_storage.get_all_users()
            else:
                # Backup file-based users
                try:
                    if os.path.exists("data/users.json"):
                        with open("data/users.json", "r", encoding="utf-8") as f:
                            users_data = json.load(f)
                            backup_data["users"] = [
                                {"telegram_id": int(k), **v} for k, v in users_data.items()
                            ]
                except Exception as e:
                    logger.warning(f"⚠️ Could not backup users: {e}")
            
            # Backup grades
            if backup_data["users"]:
                for user in backup_data["users"]:
                    telegram_id = user.get("telegram_id")
                    if telegram_id:
                        try:
                            if self.old_grade_storage and hasattr(self.old_grade_storage, 'get_grades'):
                                grades = self.old_grade_storage.get_grades(telegram_id)
                            else:
                                grades_file = f"data/grades_{telegram_id}.json"
                                if os.path.exists(grades_file):
                                    with open(grades_file, "r", encoding="utf-8") as f:
                                        grades_data = json.load(f)
                                        grades = grades_data.get("grades", [])
                                else:
                                    grades = []
                            
                            backup_data["grades"][str(telegram_id)] = grades
                        except Exception as e:
                            logger.warning(f"⚠️ Could not backup grades for user {telegram_id}: {e}")
            
            # Save backup
            backup_file = f"data/backup_v2_migration_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs("data", exist_ok=True)
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Backup created: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"❌ Error creating backup: {e}", exc_info=True)
            return None
    
    def run_migration(self):
        """Run complete migration process"""
        try:
            logger.info("🚀 Starting V2 Migration Process...")
            
            # Initialize storage systems
            self.initialize_storage_systems()
            
            # Create backup
            backup_file = self.create_backup()
            
            # Migrate users
            user_count = self.migrate_users()
            
            # Migrate grades
            grade_count = self.migrate_grades()
            
            logger.info("🎉 Migration completed successfully!")
            logger.info(f"📊 Summary:")
            logger.info(f"   - Users migrated: {user_count}")
            logger.info(f"   - Grades migrated: {grade_count}")
            logger.info(f"   - Backup file: {backup_file}")
            
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
            print("🔄 The bot is now using the new V2 storage systems.")
            print("💾 A backup of your old data has been created.")
        else:
            print("❌ Migration failed. Check the logs for details.")
            return 1
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 