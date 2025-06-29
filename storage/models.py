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
            # Create engine
            self.engine = create_engine(
                self.database_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                pool_recycle=300
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("✅ Database setup completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            raise
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close database session"""
        if session:
            session.close()
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                logger.info("✅ Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False 