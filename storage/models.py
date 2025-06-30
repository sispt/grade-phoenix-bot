"""
🗄️ Database Models for PostgreSQL
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON, text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class User(Base):
    """User model for storing user information"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)  # Will be encrypted
    token = Column(String(500), nullable=True)
    firstname = Column(String(100), nullable=True)
    lastname = Column(String(100), nullable=True)
    fullname = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
    registration_date = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username='{self.username}')>"
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "password": self.password,
            "token": self.token,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "fullname": self.fullname,
            "email": self.email,
            "registration_date": self.registration_date.isoformat() if self.registration_date else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active
        }

class Grade(Base):
    """Grade model for storing user grades"""
    __tablename__ = 'grades'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False, index=True)
    course_name = Column(String(200), nullable=False)
    course_code = Column(String(50), nullable=True)
    ects_credits = Column(String(20), nullable=True)
    practical_grade = Column(String(20), nullable=True)
    theoretical_grade = Column(String(20), nullable=True)
    final_grade = Column(String(20), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Grade(telegram_id={self.telegram_id}, course='{self.course_name}')>"
    
    def to_dict(self):
        """Convert grade to dictionary"""
        return {
            "المقرر": self.course_name,
            "كود المادة": self.course_code or "",
            "رصيد ECTS": self.ects_credits or "",
            "درجة الأعمال": self.practical_grade or "لم يتم النشر",
            "درجة النظري": self.theoretical_grade or "لم يتم النشر",
            "الدرجة": self.final_grade or "لم يتم النشر"
        }

class CredentialTest(Base):
    """Credential test cache model for tracking tested username/password combinations"""
    __tablename__ = 'credential_tests'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # Store hash for security
    test_result = Column(Boolean, nullable=False)  # True if successful, False if failed
    test_date = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    
    def __repr__(self):
        return f"<CredentialTest(username='{self.username}', result={self.test_result})>"
    
    def to_dict(self):
        """Convert credential test to dictionary"""
        return {
            "username": self.username,
            "test_result": self.test_result,
            "test_date": self.test_date.isoformat() if self.test_date else None,
            "error_message": self.error_message,
            "response_time_ms": self.response_time_ms,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address
        }

class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self, database_url):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _setup_database(self):
        """Setup database connection and create tables"""
        try:
            # Create engine with better configuration
            self.engine = create_engine(
                self.database_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                pool_recycle=300,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Test connection before creating tables
            if not self.test_connection():
                raise Exception("Database connection test failed")
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("✅ Database setup completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            raise
    
    def get_session(self):
        """Get database session with error handling"""
        try:
            return self.SessionLocal()
        except Exception as e:
            logger.error(f"❌ Failed to create database session: {e}")
            raise
    
    def close_session(self, session):
        """Close database session safely"""
        if session:
            try:
                session.close()
            except Exception as e:
                logger.error(f"❌ Error closing database session: {e}")
    
    def test_connection(self):
        """Test database connection with retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.get_session() as session:
                    session.execute(text("SELECT 1"))
                    logger.info("✅ Database connection test successful")
                    return True
            except Exception as e:
                logger.error(f"❌ Database connection test failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return False
        return False
    
    def execute_with_retry(self, operation, max_retries=3):
        """Execute database operation with retry mechanism"""
        for attempt in range(max_retries):
            try:
                return operation()
            except Exception as e:
                logger.error(f"❌ Database operation failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                raise
        return None 