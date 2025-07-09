"""
Database Models for grade-phoenix-bot
SQLAlchemy models for users and grades storage
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey, text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import logging
import os

logger = logging.getLogger(__name__)

Base = declarative_base()

class User(Base):
    """User model - stores user information"""
    __tablename__ = 'users'
    
    # Primary key is username (as requested)
    username = Column(String(100), primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    fullname = Column(String(200), nullable=True)
    firstname = Column(String(100), nullable=True)
    lastname = Column(String(100), nullable=True)
    email = Column(String(200), nullable=True)
    
    # Session management
    session_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationship to grades
    grades = relationship("Grade", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(username='{self.username}', telegram_id={self.telegram_id})>"

class Grade(Base):
    """Grade model - stores individual course grades"""
    __tablename__ = 'grades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), ForeignKey('users.username', ondelete='CASCADE'), nullable=False)
    
    # Course information
    name = Column(String(200), nullable=False)  # Course name
    code = Column(String(50), nullable=False)   # Course code
    
    # Grades
    coursework = Column(String(50), nullable=True)  # Coursework grade
    final_exam = Column(String(50), nullable=True)  # Final exam grade
    total = Column(String(50), nullable=True)       # Total grade
    
    # Additional information
    ects = Column(Float, nullable=True)             # ECTS credits
    term_name = Column(String(200), nullable=True)  # Term name
    term_id = Column(String(100), nullable=True)    # Term ID
    
    # Status
    grade_status = Column(String(50), default="Unknown")  # Published, Not Published, Unknown
    numeric_grade = Column(Float, nullable=True)          # Extracted numeric value
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationship to user
    user = relationship("User", back_populates="grades")
    
    def __repr__(self):
        return f"<Grade(username='{self.username}', course='{self.name}', total='{self.total}')>"

class DatabaseManager:
    """Database manager for MySQL connection and session management"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine"""
        try:
            # Log the database URL for debugging (without sensitive info)
            safe_url = self.database_url.replace(self.database_url.split('@')[0].split('://')[1], '***') if '@' in self.database_url else self.database_url
            logger.info(f"🔧 Initializing database engine with URL: {safe_url}")
            
            # Ensure the URL is properly formatted for MySQL
            if not self.database_url.startswith('mysql'):
                logger.error(f"❌ Invalid database URL format. Expected 'mysql://' but got: {self.database_url[:10]}...")
                raise ValueError("Database URL must start with 'mysql://' for MySQL connections")
            
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False,  # Set to True for SQL debugging
                # Explicitly specify MySQL dialect
                connect_args={"charset": "utf8mb4"}
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("✅ Database engine initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database engine: {e}")
            raise
    
    def get_session(self):
        """Get a new database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    def create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all tables (use with caution)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("✅ Database tables dropped successfully")
        except Exception as e:
            logger.error(f"❌ Failed to drop tables: {e}")
            raise
    
    def test_connection(self):
        """Test database connection"""
        try:
            if not self.engine:
                logger.error("❌ Database engine not initialized")
                return False
                
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("✅ Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False 