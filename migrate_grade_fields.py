#!/usr/bin/env python3
"""
Database Migration Script for Grade Field Names Unification
Updates the database schema and migrates existing data to use API field names consistently.
"""

import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CONFIG
from storage.models import DatabaseManager, Grade, User, Term
from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_grade_field_names():
    """Migrate existing grade data to use unified API field names"""
    
    print("🔄 Starting Grade Field Names Migration")
    print("=" * 50)
    
    try:
        # Initialize database connection
        db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
        
        if not db_manager.test_connection():
            print("❌ Database connection failed")
            return False
        
        print("✅ Database connection successful")
        
        with db_manager.get_session() as session:
            # Check if migration is needed
            try:
                # Try to access the new field names
                result = session.execute(text("SELECT name, code, coursework, final_exam, total FROM grades LIMIT 1"))
                print("✅ Database already uses new field names")
                return True
            except Exception:
                print("🔄 Database needs migration to new field names")
            
            # Get all grades that need migration
            grades = session.query(Grade).all()
            print(f"📊 Found {len(grades)} grades to migrate")
            
            if not grades:
                print("✅ No grades to migrate")
                return True
            
            migrated_count = 0
            
            for grade in grades:
                try:
                    # Create a new grade record with the new field names
                    new_grade = Grade(
                        user_id=grade.user_id,
                        term_id=grade.term_id,
                        name=grade.course_name,
                        code=grade.course_code,
                        ects_credits=grade.ects_credits,
                        coursework=grade.coursework_grade,
                        final_exam=grade.final_exam_grade,
                        total=grade.total_grade_value,
                        numeric_grade=grade.numeric_grade,
                        grade_status=grade.grade_status,
                        created_at=grade.created_at,
                        updated_at=grade.updated_at
                    )
                    
                    # Delete the old grade record
                    session.delete(grade)
                    
                    # Add the new grade record
                    session.add(new_grade)
                    migrated_count += 1
                    
                    if migrated_count % 100 == 0:
                        print(f"   Migrated {migrated_count}/{len(grades)} grades...")
                        
                except Exception as e:
                    logger.error(f"❌ Error migrating grade {grade.id}: {e}")
                    session.rollback()
                    return False
            
            # Commit all changes
            session.commit()
            print(f"✅ Successfully migrated {migrated_count} grades")
            
            # Verify migration
            try:
                result = session.execute(text("SELECT name, code, coursework, final_exam, total FROM grades LIMIT 1"))
                print("✅ Migration verification successful")
            except Exception as e:
                print(f"❌ Migration verification failed: {e}")
                return False
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        return False

def create_new_tables():
    """Create new tables with the updated schema"""
    
    print("\n🗄️ Creating new tables with updated schema")
    print("=" * 50)
    
    try:
        db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
        
        # Create all tables with the new schema
        db_manager.create_all_tables()
        print("✅ New tables created successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create new tables: {e}", exc_info=True)
        return False

def backup_existing_data():
    """Create a backup of existing grade data"""
    
    print("\n💾 Creating backup of existing data")
    print("=" * 50)
    
    try:
        db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
        
        with db_manager.get_session() as session:
            # Get all grades
            grades = session.query(Grade).all()
            
            if not grades:
                print("✅ No grades to backup")
                return True
            
            # Create backup file
            backup_file = f"grade_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            import json
            backup_data = []
            
            for grade in grades:
                backup_data.append({
                    "id": grade.id,
                    "user_id": grade.user_id,
                    "term_id": grade.term_id,
                    "course_name": grade.course_name,
                    "course_code": grade.course_code,
                    "ects_credits": float(grade.ects_credits) if grade.ects_credits else None,
                    "coursework_grade": grade.coursework_grade,
                    "final_exam_grade": grade.final_exam_grade,
                    "total_grade_value": grade.total_grade_value,
                    "numeric_grade": float(grade.numeric_grade) if grade.numeric_grade else None,
                    "grade_status": grade.grade_status,
                    "created_at": grade.created_at.isoformat() if grade.created_at else None,
                    "updated_at": grade.updated_at.isoformat() if grade.updated_at else None,
                })
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Backup created: {backup_file}")
            print(f"📊 Backed up {len(backup_data)} grades")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}", exc_info=True)
        return False

def main():
    """Main migration function"""
    
    print("🎓 Grade Field Names Migration Tool")
    print("=" * 50)
    print("This tool will:")
    print("1. Create a backup of existing grade data")
    print("2. Create new tables with updated schema")
    print("3. Migrate existing data to use unified field names")
    print("=" * 50)
    
    # Ask for confirmation
    response = input("Do you want to proceed with the migration? (y/N): ")
    if response.lower() != 'y':
        print("❌ Migration cancelled")
        return
    
    # Step 1: Create backup
    if not backup_existing_data():
        print("❌ Backup failed, aborting migration")
        return
    
    # Step 2: Create new tables
    if not create_new_tables():
        print("❌ Failed to create new tables, aborting migration")
        return
    
    # Step 3: Migrate data
    if not migrate_grade_field_names():
        print("❌ Data migration failed")
        return
    
    print("\n🎉 Migration completed successfully!")
    print("=" * 50)
    print("✅ All grade data now uses unified API field names")
    print("✅ Grade notifications should work correctly")
    print("✅ No more field name mapping needed")

if __name__ == "__main__":
    main() 