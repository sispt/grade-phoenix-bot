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
    
    # New fields for permanent/temporary session
    encrypted_password = Column(Text, nullable=True)
    password_stored = Column(Boolean, default=False, nullable=False)
    password_consent_given = Column(Boolean, default=False, nullable=False)
    
    # Relationships
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
    
    # Indexes
    __table_args__ = (
        Index('idx_term_id', 'term_id'),
        Index('idx_term_current', 'is_current'),
        Index('idx_term_academic_year', 'academic_year'),
    )

    def __repr__(self):
        return f"<Term(term_id='{self.term_id}', name='{self.name}', current={self.is_current})>"


class Grade(Base):
    """Grade model for storing individual course grades in the database (username_unique as FK, unified terminology)"""

    __tablename__ = "grades"

    id = Column(Integer, primary_key=True)
    username_unique = Column(String(100), ForeignKey("users.username_unique", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=True, index=True)
    ects = Column(Numeric(3, 1), nullable=True)
    coursework = Column(String(20), nullable=True)
    final_exam = Column(String(20), nullable=True)
    total = Column(String(20), nullable=True)
    numeric_grade = Column(Numeric(5, 2), nullable=True)
    grade_status = Column(String(20), default="Not Published", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_grade_username_unique', 'username_unique'),
        Index('idx_grade_code', 'code'),
        Index('idx_grade_status', 'grade_status'),
        Index('idx_grade_numeric', 'numeric_grade'),
        UniqueConstraint('username_unique', 'code', name='unique_user_course'),
    )

    def __repr__(self):
        return f"<Grade(username_unique={self.username_unique}, code='{self.code}', name='{self.name}', grade='{self.total}')>"


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


class GradeFailsafe(Base):
    """Failsafe grade table: no FKs, no constraints, always works."""
    __tablename__ = "grades_failsafe"
    id = Column(Integer, primary_key=True)
    username_unique = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=True, index=True)
    ects = Column(Numeric(3, 1), nullable=True)
    coursework = Column(String(20), nullable=True)
    final_exam = Column(String(20), nullable=True)
    total = Column(String(20), nullable=True)
    numeric_grade = Column(Numeric(5, 2), nullable=True)
    grade_status = Column(String(20), default="Not Published", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<GradeFailsafe(username_unique={self.username_unique}, code='{self.code}', name='{self.name}', grade='{self.total}')>"

class GradeFailsafeStorage:
    def __init__(self, database_url):
        from storage.models import DatabaseManager, GradeFailsafe
        self.db_manager = DatabaseManager(database_url)
        self.GradeFailsafe = GradeFailsafe
        self.db_manager.create_all_tables()
    def save_grades(self, username_unique, grades_data):
        print("DEBUG: grades_data =", grades_data)  # Debug print to check input
        from datetime import datetime, timezone
        with self.db_manager.get_session() as session:
            for grade_data in grades_data:
                grade = self.GradeFailsafe(
                    username_unique=username_unique,
                    name=grade_data.get("name", ""),
                    code=grade_data.get("code", ""),
                    ects=grade_data.get("ects"),
                    coursework=grade_data.get("coursework"),
                    final_exam=grade_data.get("final_exam"),
                    total=grade_data.get("total"),
                    numeric_grade=grade_data.get("numeric_grade"),
                    grade_status=grade_data.get("grade_status", "Unknown"),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(grade)
            session.commit()
    def get_user_grades(self, username_unique):
        with self.db_manager.get_session() as session:
            grades = session.query(self.GradeFailsafe).filter_by(username_unique=username_unique).all()
            return [
                {
                    "name": g.name,
                    "code": g.code,
                    "ects": g.ects,
                    "coursework": g.coursework,
                    "final_exam": g.final_exam,
                    "total": g.total,
                    "numeric_grade": g.numeric_grade,
                    "grade_status": g.grade_status,
                    "created_at": g.created_at.isoformat() if g.created_at is not None else None,
                    "updated_at": g.updated_at.isoformat() if g.updated_at is not None else None,
                }
                for g in grades
            ]


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
            Base.metadata.create_all(self.engine)
            logger.info("✅ All database tables created successfully.")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")

    @staticmethod
    def create_all_tables_for_url(database_url: str):
        """Utility to create all tables for any given database URL."""
        from sqlalchemy import create_engine
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)
        print(f"✅ Ran create_all_tables() for {database_url}")

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
            session.commit()  # Commit if no exception
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Database session error: {e}", exc_info=True)
            raise
        finally:
            session.close()

if __name__ == "__main__":
    import os
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Please set the DATABASE_URL environment variable.")
    else:
        DatabaseManager.create_all_tables_for_url(db_url)
