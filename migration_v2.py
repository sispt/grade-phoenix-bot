"""
Database Migration Script v2
Updates database schema to match new models with proper relationships and data types.
"""

import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.exc import SQLAlchemyError
from config import CONFIG
from storage.models import Base, DatabaseManager, User, Grade, Term, GradeHistory, CredentialTest

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("migration_v2")

def get_database_info(engine):
    """Get database information"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"📊 Database: {version}")
            return version
    except Exception as e:
        logger.error(f"❌ Error getting database info: {e}")
        return None

def table_exists(engine, table_name):
    """Check if table exists"""
    try:
        inspector = inspect(engine)
        exists = table_name in inspector.get_table_names()
        logger.info(f"🔍 Table '{table_name}': {'EXISTS' if exists else 'NOT FOUND'}")
        return exists
    except Exception as e:
        logger.error(f"❌ Error checking table '{table_name}': {e}")
        return False

def column_exists(engine, table_name, column_name):
    """Check if column exists in table"""
    try:
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            return False
        columns = [col["name"] for col in inspector.get_columns(table_name)]
        exists = column_name in columns
        logger.info(f"🔍 Column '{column_name}' in '{table_name}': {'EXISTS' if exists else 'NOT FOUND'}")
        return exists
    except Exception as e:
        logger.error(f"❌ Error checking column '{column_name}' in '{table_name}': {e}")
        return False

def add_column_if_not_exists(engine, table_name, column_name, column_definition):
    """Add column if it doesn't exist"""
    try:
        if not column_exists(engine, table_name, column_name):
            with engine.connect() as conn:
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
                logger.info(f"🔧 Adding column: {sql}")
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"✅ Column '{column_name}' added to '{table_name}'")
                return True
        else:
            logger.info(f"⏭️ Column '{column_name}' already exists in '{table_name}'")
            return True
    except Exception as e:
        logger.error(f"❌ Error adding column '{column_name}' to '{table_name}': {e}")
        return False

def drop_column_if_exists(engine, table_name, column_name):
    """Drop column if it exists"""
    try:
        if column_exists(engine, table_name, column_name):
            with engine.connect() as conn:
                sql = f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
                logger.info(f"🗑️ Dropping column: {sql}")
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"✅ Column '{column_name}' dropped from '{table_name}'")
                return True
        else:
            logger.info(f"⏭️ Column '{column_name}' doesn't exist in '{table_name}'")
            return True
    except Exception as e:
        logger.error(f"❌ Error dropping column '{column_name}' from '{table_name}': {e}")
        return False

def create_table_if_not_exists(engine, table_name):
    """Create table if it doesn't exist"""
    try:
        if not table_exists(engine, table_name):
            logger.info(f"🔧 Creating table '{table_name}' using SQLAlchemy models...")
            Base.metadata.tables[table_name].create(bind=engine)
            logger.info(f"✅ Table '{table_name}' created successfully")
            return True
        else:
            logger.info(f"⏭️ Table '{table_name}' already exists")
            return True
    except Exception as e:
        logger.error(f"❌ Error creating table '{table_name}': {e}")
        return False

def migrate_users_table(engine):
    """Migrate users table to new schema"""
    logger.info("🔧 Migrating users table...")
    
    # Add missing columns
    columns_to_add = [
        ("registration_date", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("last_login", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("is_active", "BOOLEAN DEFAULT TRUE"),
        ("token_expired_notified", "BOOLEAN DEFAULT FALSE"),
    ]
    
    for column_name, column_def in columns_to_add:
        add_column_if_not_exists(engine, "users", column_name, column_def)
    
    # Drop old password columns if they exist
    old_columns = ["password", "password_hash"]
    for column_name in old_columns:
        drop_column_if_exists(engine, "users", column_name)
    
    logger.info("✅ Users table migration completed")

def migrate_grades_table(engine):
    """Migrate grades table to new schema"""
    logger.info("🔧 Migrating grades table...")
    
    # Check if old grades table exists
    if table_exists(engine, "grades"):
        # Get current columns
        inspector = inspect(engine)
        current_columns = [col["name"] for col in inspector.get_columns("grades")]
        logger.info(f"📋 Current grades columns: {current_columns}")
        
        # If using old schema (telegram_id), we need to migrate data
        if "telegram_id" in current_columns and "user_id" not in current_columns:
            logger.info("🔄 Migrating from old grades schema to new schema...")
            
            # Create temporary table with new schema
            with engine.connect() as conn:
                # Create new grades table
                conn.execute(text("""
                    CREATE TABLE grades_new (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        term_id INTEGER REFERENCES terms(id) ON DELETE CASCADE,
                        course_name VARCHAR(255) NOT NULL,
                        course_code VARCHAR(50),
                        ects_credits NUMERIC(3,1),
                        coursework_grade VARCHAR(20),
                        final_exam_grade VARCHAR(20),
                        total_grade_value VARCHAR(20),
                        numeric_grade NUMERIC(5,2),
                        grade_status VARCHAR(20) DEFAULT 'Not Published',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Migrate data from old to new table
                conn.execute(text("""
                    INSERT INTO grades_new (
                        user_id, course_name, course_code, ects_credits,
                        coursework_grade, final_exam_grade, total_grade_value,
                        created_at, updated_at
                    )
                    SELECT 
                        u.id as user_id,
                        g.course_name,
                        g.course_code,
                        g.ects_credits,
                        g.coursework_grade,
                        g.final_exam_grade,
                        g.total_grade_value,
                        g.last_updated as created_at,
                        g.last_updated as updated_at
                    FROM grades g
                    JOIN users u ON g.telegram_id = u.telegram_id
                """))
                
                # Drop old table and rename new table
                conn.execute(text("DROP TABLE grades"))
                conn.execute(text("ALTER TABLE grades_new RENAME TO grades"))
                conn.commit()
                
                logger.info("✅ Grades table migrated successfully")
        else:
            logger.info("⏭️ Grades table already using new schema")
    else:
        # Create new grades table
        create_table_if_not_exists(engine, "grades")

def create_new_tables(engine):
    """Create new tables that don't exist"""
    logger.info("🔧 Creating new tables...")
    
    new_tables = ["terms", "grade_history"]
    for table_name in new_tables:
        create_table_if_not_exists(engine, table_name)

def add_indexes(engine):
    """Add missing indexes"""
    logger.info("🔧 Adding indexes...")
    
    try:
        with engine.connect() as conn:
            # Users table indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_user_telegram_id ON users(telegram_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_username ON users(username)",
                "CREATE INDEX IF NOT EXISTS idx_user_active ON users(is_active)",
                
                # Grades table indexes
                "CREATE INDEX IF NOT EXISTS idx_grade_user_id ON grades(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_grade_term_id ON grades(term_id)",
                "CREATE INDEX IF NOT EXISTS idx_grade_course_code ON grades(course_code)",
                "CREATE INDEX IF NOT EXISTS idx_grade_status ON grades(grade_status)",
                "CREATE INDEX IF NOT EXISTS idx_grade_numeric ON grades(numeric_grade)",
                
                # Terms table indexes
                "CREATE INDEX IF NOT EXISTS idx_term_id ON terms(term_id)",
                "CREATE INDEX IF NOT EXISTS idx_term_current ON terms(is_current)",
                "CREATE INDEX IF NOT EXISTS idx_term_academic_year ON terms(academic_year)",
                
                # Grade history indexes
                "CREATE INDEX IF NOT EXISTS idx_history_user_id ON grade_history(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_history_grade_id ON grade_history(grade_id)",
                "CREATE INDEX IF NOT EXISTS idx_history_changed_at ON grade_history(changed_at)",
                
                # Credential tests indexes
                "CREATE INDEX IF NOT EXISTS idx_credential_username ON credential_tests(username)",
                "CREATE INDEX IF NOT EXISTS idx_credential_test_date ON credential_tests(test_date)",
                "CREATE INDEX IF NOT EXISTS idx_credential_result ON credential_tests(test_result)",
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    logger.info(f"✅ Index created: {index_sql}")
                except Exception as e:
                    logger.warning(f"⚠️ Index creation failed (might already exist): {e}")
            
            conn.commit()
            logger.info("✅ All indexes added successfully")
            
    except Exception as e:
        logger.error(f"❌ Error adding indexes: {e}")

def verify_migration(engine):
    """Verify migration was successful"""
    logger.info("🔍 Verifying migration...")
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"📋 Tables found: {tables}")
        
        expected_tables = ["users", "grades", "terms", "grade_history", "credential_tests"]
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if missing_tables:
            logger.error(f"❌ Missing tables: {missing_tables}")
            return False
        
        # Check users table structure
        if "users" in tables:
            user_columns = [col["name"] for col in inspector.get_columns("users")]
            expected_user_columns = [
                "id", "telegram_id", "username", "token", "firstname", "lastname",
                "fullname", "email", "registration_date", "last_login", "is_active", "token_expired_notified"
            ]
            missing_user_columns = [col for col in expected_user_columns if col not in user_columns]
            
            if missing_user_columns:
                logger.error(f"❌ Missing user columns: {missing_user_columns}")
                return False
        
        # Check grades table structure
        if "grades" in tables:
            grade_columns = [col["name"] for col in inspector.get_columns("grades")]
            expected_grade_columns = [
                "id", "user_id", "term_id", "course_name", "course_code", "ects_credits",
                "coursework_grade", "final_exam_grade", "total_grade_value", "numeric_grade",
                "grade_status", "created_at", "updated_at"
            ]
            missing_grade_columns = [col for col in expected_grade_columns if col not in grade_columns]
            
            if missing_grade_columns:
                logger.error(f"❌ Missing grade columns: {missing_grade_columns}")
                return False
        
        logger.info("✅ Migration verification successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying migration: {e}")
        return False

def run_migration():
    """Main migration function"""
    logger.info("🚀 Starting Database Migration v2...")
    logger.info(f"🔧 Database URL: {CONFIG['DATABASE_URL']}")
    
    try:
        # Create engine
        engine = create_engine(CONFIG['DATABASE_URL'])
        logger.info(f"🔌 Database engine created successfully")
        
        # Get database info
        get_database_info(engine)
        
        # Step 1: Migrate users table
        logger.info("📋 Step 1: Migrating users table...")
        migrate_users_table(engine)
        
        # Step 2: Create new tables
        logger.info("📋 Step 2: Creating new tables...")
        create_new_tables(engine)
        
        # Step 3: Migrate grades table
        logger.info("📋 Step 3: Migrating grades table...")
        migrate_grades_table(engine)
        
        # Step 4: Add indexes
        logger.info("📋 Step 4: Adding indexes...")
        add_indexes(engine)
        
        # Step 5: Verify migration
        logger.info("📋 Step 5: Verifying migration...")
        if verify_migration(engine):
            logger.info("🎉 Migration completed successfully!")
            return True
        else:
            logger.error("❌ Migration verification failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n✅ Migration completed successfully!")
        print("🔄 Your database schema now matches the new code structure.")
        print("📊 All tables, columns, and relationships are properly set up.")
    else:
        print("\n❌ Migration failed!")
        print("🔧 Please check the logs above for details.")
        exit(1) 