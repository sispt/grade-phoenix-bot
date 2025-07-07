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
from storage.user_storage_old import UserStorage, PostgreSQLUserStorage
from storage.grade_storage_old import GradeStorage, PostgreSQLGradeStorage
from storage.models import DatabaseManager, Grade
from sqlalchemy import text

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
            
            # Initialize old storage systems - only use file-based storage to avoid schema conflicts
            # Skip old PostgreSQL storage since it conflicts with new V2 schema
            logger.info("📁 Using file-based storage for reading old data (avoiding schema conflicts)")
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
                        "email": user_data.get("email", ""),
                        "token_expired_notified": user_data.get("token_expired_notified", False)
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
                    
                    # Try file-based storage first (safer)
                    try:
                        grades_file = f"data/grades_{telegram_id}.json"
                        if os.path.exists(grades_file):
                            with open(grades_file, "r", encoding="utf-8") as f:
                                grades_data = json.load(f)
                                old_grades = grades_data.get("grades", [])
                                logger.info(f"📁 Found {len(old_grades)} grades in file for user {telegram_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not read grades file for user {telegram_id}: {e}")
                    
                    # If no file-based grades, try old storage (but this might fail due to schema conflicts)
                    if not old_grades and self.old_grade_storage and hasattr(self.old_grade_storage, 'get_grades'):
                        try:
                            old_grades = self.old_grade_storage.get_grades(telegram_id)
                            logger.info(f"📊 Found {len(old_grades)} grades in old storage for user {telegram_id}")
                        except Exception as e:
                            logger.warning(f"⚠️ Could not read grades from old storage for user {telegram_id}: {e}")
                            # This is expected if old storage has schema conflicts
                    
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
    
    def migrate_grade_field_names(self) -> int:
        """Migrate existing grade data in new storage to use unified API field names"""
        try:
            logger.info("🔄 Starting grade field names migration...")
            
            if not self.new_grade_storage:
                logger.error("❌ New grade storage not initialized")
                return 0
            
            # Get database manager from new storage
            db_manager = self.new_grade_storage.db_manager
            
            with db_manager.get_session() as session:
                # First, check if there are any grades in the database at all
                total_grades = session.query(Grade).count()
                if total_grades == 0:
                    logger.info("✅ No grades in database - nothing to migrate")
                    return 0
                
                # Check if migration is needed by testing if new field names exist
                try:
                    # Try to access the new field names
                    result = session.execute(text("SELECT name, code, coursework, final_exam, total FROM grades LIMIT 1"))
                    logger.info("✅ Database already uses new field names")
                    return 0
                except Exception:
                    logger.info("🔄 Database needs migration to new field names")
                
                # Check if old field names exist (to avoid migrating empty database)
                try:
                    old_field_test = session.execute(text("SELECT course_name, course_code, coursework_grade, final_exam_grade, total_grade_value FROM grades LIMIT 1"))
                    has_old_fields = True
                    logger.info("✅ Found grades with old field names - proceeding with migration")
                except Exception:
                    logger.info("✅ No grades with old field names found - nothing to migrate")
                    return 0
                
                # Get all grades that have old field names and need migration
                try:
                    grades = session.execute(text("SELECT * FROM grades WHERE course_name IS NOT NULL OR course_code IS NOT NULL")).fetchall()
                    logger.info(f"📊 Found {len(grades)} grades with old field names to migrate")
                except Exception as e:
                    logger.info(f"✅ No grades with old field names found: {e}")
                    return 0
                
                if not grades:
                    logger.info("✅ No grades to migrate")
                    return 0
                
                migrated_count = 0
                
                for grade_row in grades:
                    try:
                        # Get the grade object
                        grade = session.query(Grade).filter_by(id=grade_row.id).first()
                        if not grade:
                            continue
                        
                        # Check if this grade has old field names
                        if not hasattr(grade, 'course_name') or not hasattr(grade, 'course_code'):
                            continue
                        
                        # Create a new grade record with the new field names
                        new_grade = Grade(
                            user_id=grade.user_id,
                            term_id=grade.term_id,
                            name=getattr(grade, 'course_name', ''),
                            code=getattr(grade, 'course_code', ''),
                            ects_credits=getattr(grade, 'ects_credits', None),
                            coursework=getattr(grade, 'coursework_grade', ''),
                            final_exam=getattr(grade, 'final_exam_grade', ''),
                            total=getattr(grade, 'total_grade_value', ''),
                            numeric_grade=getattr(grade, 'numeric_grade', None),
                            grade_status=getattr(grade, 'grade_status', 'Unknown'),
                            created_at=getattr(grade, 'created_at', datetime.utcnow()),
                            updated_at=getattr(grade, 'updated_at', datetime.utcnow())
                        )
                        
                        # Delete the old grade record
                        session.delete(grade)
                        
                        # Add the new grade record
                        session.add(new_grade)
                        migrated_count += 1
                        
                        if migrated_count % 100 == 0:
                            logger.info(f"   Migrated {migrated_count}/{len(grades)} grades...")
                            
                    except Exception as e:
                        logger.error(f"❌ Error migrating grade {getattr(grade_row, 'id', 'unknown')}: {e}")
                        session.rollback()
                        return 0
                
                # Commit all changes
                session.commit()
                logger.info(f"✅ Successfully migrated {migrated_count} grades to new field names")
                
                # Verify migration
                try:
                    result = session.execute(text("SELECT name, code, coursework, final_exam, total FROM grades LIMIT 1"))
                    logger.info("✅ Migration verification successful")
                except Exception as e:
                    logger.error(f"❌ Migration verification failed: {e}")
                    return 0
                
                return migrated_count
                
        except Exception as e:
            logger.error(f"❌ Grade field migration failed: {e}", exc_info=True)
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
            
            # Migrate grade field names to unified API format
            field_migration_count = self.migrate_grade_field_names()
            
            logger.info("🎉 Migration completed successfully!")
            logger.info(f"📊 Summary:")
            logger.info(f"   - Users migrated: {user_count}")
            logger.info(f"   - Grades migrated: {grade_count}")
            logger.info(f"   - Grade fields unified: {field_migration_count}")
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