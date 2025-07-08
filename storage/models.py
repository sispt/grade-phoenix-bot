"""
SQLAlchemy ORM Models for Database Storage
Clean, well-structured database schema
"""

import logging
from datetime import datetime
from contextlib import contextmanager
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    BigInteger,
    ForeignKey,
    Text,
    Numeric,
    Index,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

Base = declarative_base()


class User(Base):
    """User model for storing user information in the database"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False, index=True)
    token = Column(String(500), nullable=True)
    firstname = Column(String(100), nullable=True)
    lastname = Column(String(100), nullable=True)
    fullname = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
    registration_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    token_expired_notified = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    grades = relationship("Grade", back_populates="user", cascade="all, delete-orphan")
    grade_history = relationship("GradeHistory", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_telegram_id', 'telegram_id'),
        Index('idx_user_username', 'username'),
        Index('idx_user_active', 'is_active'),
    )

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username='{self.username}')>"


class Term(Base):
    """Term/Semester model for organizing grades by academic periods"""

    __tablename__ = "terms"

    id = Column(Integer, primary_key=True)
    term_id = Column(String(50), unique=True, nullable=False, index=True)  # University term ID
    name = Column(String(200), nullable=False)  # e.g., "الفصل الأول 2024-2025"
    academic_year = Column(String(20), nullable=True)  # e.g., "2024-2025"
    is_current = Column(Boolean, default=False, nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    grades = relationship("Grade", back_populates="term")
    
    # Indexes
    __table_args__ = (
        Index('idx_term_id', 'term_id'),
        Index('idx_term_current', 'is_current'),
        Index('idx_term_academic_year', 'academic_year'),
    )

    def __repr__(self):
        return f"<Term(term_id='{self.term_id}', name='{self.name}', current={self.is_current})>"


class Grade(Base):
    """Grade model for storing individual course grades in the database"""

    __tablename__ = "grades"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    term_id = Column(Integer, ForeignKey("terms.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Course information
    course_name = Column(String(255), nullable=False, index=True)
    course_code = Column(String(50), nullable=True, index=True)
    ects_credits = Column(Numeric(3, 1), nullable=True)  # e.g., 3.0
    
    # Grade values (stored as strings for flexibility with Arabic text)
    coursework_grade = Column(String(20), nullable=True)
    final_exam_grade = Column(String(20), nullable=True)
    total_grade_value = Column(String(20), nullable=True)  # e.g., "87 %" or "لم يتم النشر"

    # Numeric grade for calculations (extracted from total_grade_value)
    numeric_grade = Column(Numeric(5, 2), nullable=True)  # e.g., 87.00
    
    # Grade status
    grade_status = Column(String(20), default="Not Published", nullable=False)  # Published, Not Published, Unknown
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="grades")
    term = relationship("Term", back_populates="grades")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_grade_user_id', 'user_id'),
        Index('idx_grade_term_id', 'term_id'),
        Index('idx_grade_course_code', 'course_code'),
        Index('idx_grade_status', 'grade_status'),
        Index('idx_grade_numeric', 'numeric_grade'),
        UniqueConstraint('user_id', 'course_code', 'term_id', name='unique_user_course_term'),
    )

    def __repr__(self):
        return f"<Grade(user_id={self.user_id}, course='{self.course_name}', grade='{self.total_grade_value}')>"


class GradeHistory(Base):
    """Grade history for tracking changes over time"""

    __tablename__ = "grade_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    grade_id = Column(Integer, ForeignKey("grades.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Previous values
    previous_total_grade = Column(String(20), nullable=True)
    previous_numeric_grade = Column(Numeric(5, 2), nullable=True)
    previous_status = Column(String(20), nullable=True)
    
    # Change metadata
    change_type = Column(String(20), nullable=False)  # Created, Updated, Deleted
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="grade_history")
    grade = relationship("Grade")
    
    # Indexes
    __table_args__ = (
        Index('idx_history_user_id', 'user_id'),
        Index('idx_history_grade_id', 'grade_id'),
        Index('idx_history_changed_at', 'changed_at'),
    )

    def __repr__(self):
        return f"<GradeHistory(user_id={self.user_id}, grade_id={self.grade_id}, change='{self.change_type}')>"


class CredentialTest(Base):
    """Credential test cache model for storing test results"""

    __tablename__ = "credential_tests"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, index=True)
    test_result = Column(Boolean, nullable=False)
    test_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    error_message = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    
    # Indexes
    __table_args__ = (
        Index('idx_credential_username', 'username'),
        Index('idx_credential_test_date', 'test_date'),
        Index('idx_credential_result', 'test_result'),
    )

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "test_result": self.test_result,
            "test_date": (
                self.test_date.isoformat() if self.test_date is not None else None
            ),
            "error_message": self.error_message,
            "response_time_ms": self.response_time_ms,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
        }

    def __repr__(self):
        return f"<CredentialTest(username='{self.username}', test_result={self.test_result}, test_date='{self.test_date}')>"


class DatabaseManager:
    """Manages database connection and sessions"""

    def __init__(self, database_url):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def test_connection(self):
        try:
            # Try to connect and execute a dummy query
            with self.engine.connect() as connection:
                # Check if at least one table is accessible (e.g., 'users')
                # This explicitly tries to access a table, not just connect.
                connection.execute(Base.metadata.tables["users"].select().limit(1))
            logger.info("✅ Database connection successful and tables accessible.")
            return True
        except Exception as e:
            logger.error(
                f"❌ Database connection or table access failed: {e}", exc_info=True
            )
            return False

    def create_all_tables(self):
        """Create all tables if they don't exist"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ All database tables created successfully.")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating database tables: {e}", exc_info=True)
            return False

    def drop_all_tables(self):
        """Drop all tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("✅ All database tables dropped successfully.")
            return True
        except Exception as e:
            logger.error(f"❌ Error dropping database tables: {e}", exc_info=True)
            return False

    @contextmanager
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Database session error: {e}", exc_info=True)
            raise
        finally:
            session.close()
