#!/usr/bin/env python3
"""
🗄️ Database Migration Script
Handles database setup and migrations for PostgreSQL
"""
import os
import sys
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CONFIG
from storage.models import DatabaseManager, Base, User, Grade
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run database migrations"""
    try:
        logger.info("🚀 Starting database migration...")
        
        # Check if PostgreSQL is configured
        if not CONFIG.get("USE_POSTGRESQL", False):
            logger.info("📁 Using file-based storage, no migration needed")
            return True
        
        # Initialize database manager
        db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
        
        # Test connection
        if not db_manager.test_connection():
            logger.error("❌ Database connection failed")
            return False
        
        # Create tables
        logger.info("📋 Creating database tables...")
        Base.metadata.create_all(bind=db_manager.engine)
        logger.info("✅ Database tables created successfully")
        
        # Verify tables exist
        with db_manager.get_session() as session:
            # Check if users table exists
            result = session.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"))
            users_table_exists = result.scalar()
            
            # Check if grades table exists
            result = session.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'grades')"))
            grades_table_exists = result.scalar()
            
            if users_table_exists and grades_table_exists:
                logger.info("✅ All tables verified successfully")
            else:
                logger.error("❌ Some tables are missing")
                return False
        
        logger.info("🎉 Database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    try:
        logger.info("🧪 Creating sample data...")
        
        if not CONFIG.get("USE_POSTGRESQL", False):
            logger.info("📁 Using file-based storage, skipping sample data")
            return True
        
        db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
        
        with db_manager.get_session() as session:
            # Check if sample data already exists
            existing_users = session.query(User).count()
            if existing_users > 0:
                logger.info("📊 Sample data already exists, skipping...")
                return True
            
            # Create sample user
            sample_user = User(
                telegram_id=123456789,
                username="SAMPLE_USER",
                password="sample_password",
                token="sample_token",
                firstname="عينة",
                lastname="مستخدم",
                fullname="عينة مستخدم",
                email="sample@student.shamuniversity.com",
                registration_date=datetime.utcnow(),
                last_login=datetime.utcnow(),
                is_active=True
            )
            session.add(sample_user)
            
            # Create sample grades
            sample_grades = [
                Grade(
                    telegram_id=123456789,
                    course_name="برمجة متقدمة",
                    course_code="CS301",
                    ects_credits="3",
                    practical_grade="85",
                    theoretical_grade="88",
                    final_grade="87",
                    last_updated=datetime.utcnow()
                ),
                Grade(
                    telegram_id=123456789,
                    course_name="قواعد البيانات",
                    course_code="CS302",
                    ects_credits="3",
                    practical_grade="92",
                    theoretical_grade="90",
                    final_grade="91",
                    last_updated=datetime.utcnow()
                )
            ]
            
            for grade in sample_grades:
                session.add(grade)
            
            session.commit()
            logger.info("✅ Sample data created successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Sample data creation failed: {e}")
        return False

def check_database_status():
    """Check database status and statistics"""
    try:
        logger.info("🔍 Checking database status...")
        
        if not CONFIG.get("USE_POSTGRESQL", False):
            logger.info("📁 Using file-based storage")
            return True
        
        db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
        
        with db_manager.get_session() as session:
            # Get table counts
            users_count = session.query(User).count()
            grades_count = session.query(Grade).count()
            
            # Get unique users with grades
            users_with_grades = session.query(Grade.telegram_id).distinct().count()
            
            logger.info(f"📊 Database Statistics:")
            logger.info(f"   • Total users: {users_count}")
            logger.info(f"   • Total grades: {grades_count}")
            logger.info(f"   • Users with grades: {users_with_grades}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Database status check failed: {e}")
        return False

def main():
    """Main migration function"""
    logger.info("🗄️ Database Migration Tool")
    logger.info("=" * 50)
    
    # Check configuration
    logger.info(f"🔧 Configuration:")
    logger.info(f"   • Database URL: {CONFIG['DATABASE_URL'][:50]}...")
    logger.info(f"   • Use PostgreSQL: {CONFIG.get('USE_POSTGRESQL', False)}")
    
    # Run migrations
    if not run_migrations():
        logger.error("❌ Migration failed")
        sys.exit(1)
    
    # Create sample data (optional)
    if os.getenv("CREATE_SAMPLE_DATA", "false").lower() == "true":
        if not create_sample_data():
            logger.warning("⚠️ Sample data creation failed")
    
    # Check database status
    if not check_database_status():
        logger.error("❌ Database status check failed")
        sys.exit(1)
    
    logger.info("🎉 All operations completed successfully!")

if __name__ == "__main__":
    main() 