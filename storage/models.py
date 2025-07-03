"""
SQLAlchemy ORM Models for Database Storage
"""

import logging
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    BigInteger,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

Base = declarative_base()


class User(Base):
    """User model for storing user information in the database"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(
        BigInteger, unique=True, nullable=False, index=True
    )  # CRITICAL: BigInteger for Telegram IDs
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=True)  # Password is not stored; field kept for legacy compatibility
    token = Column(String(500), nullable=True)
    firstname = Column(String(100), nullable=True)
    lastname = Column(String(100), nullable=True)
    fullname = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
    registration_date = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username='{self.username}')>"


class Grade(Base):
    """Grade model for storing individual course grades in the database"""

    __tablename__ = "grades"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )  # CRITICAL: BigInteger with CASCADE

    # --- CRITICAL: ADDED ALL GRADE DETAIL COLUMNS ---
    course_name = Column(String(255), nullable=False)
    course_code = Column(String(50), nullable=True)
    ects_credits = Column(String(10), nullable=True)
    coursework_grade = Column(String(20), nullable=True)
    final_exam_grade = Column(String(20), nullable=True)
    total_grade_value = Column(
        String(20), nullable=True
    )  # Stores "87 %" or "لم يتم النشر"

    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Grade(telegram_id={self.telegram_id}, course_name='{self.course_name}', total_grade='{self.total_grade_value}')>"


class CredentialTest(Base):
    """Credential test cache model for storing test results"""

    __tablename__ = "credential_tests"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, index=True)
    test_result = Column(Boolean, nullable=False)
    test_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    error_message = Column(String(500), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible

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
