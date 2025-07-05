"""
📊 Grade Storage V2 - Clean Implementation
Handles grade data storage with PostgreSQL
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from decimal import Decimal
import re

from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, Index, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

Base = declarative_base()


class Term(Base):
    """Term/Semester model"""
    
    __tablename__ = "terms"
    
    id = Column(Integer, primary_key=True)
    term_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    academic_year = Column(String(20), nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    grades = relationship("Grade", back_populates="term")
    
    # Indexes
    __table_args__ = (
        Index('idx_term_id', 'term_id'),
        Index('idx_term_current', 'is_current'),
    )


class Grade(Base):
    """Grade model for individual course grades"""
    
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    term_id = Column(Integer, ForeignKey("terms.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Course information
    course_name = Column(String(255), nullable=False, index=True)
    course_code = Column(String(50), nullable=True, index=True)
    ects_credits = Column(Numeric(3, 1), nullable=True)
    
    # Grade values
    coursework_grade = Column(String(20), nullable=True)
    final_exam_grade = Column(String(20), nullable=True)
    total_grade_value = Column(String(20), nullable=True)
    numeric_grade = Column(Numeric(5, 2), nullable=True)
    
    # Grade status
    grade_status = Column(String(20), default="Not Published", nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    term = relationship("Term", back_populates="grades")
    
    # Indexes
    __table_args__ = (
        Index('idx_grade_user_id', 'user_id'),
        Index('idx_grade_term_id', 'term_id'),
        Index('idx_grade_course_code', 'course_code'),
        Index('idx_grade_status', 'grade_status'),
        Index('idx_grade_numeric', 'numeric_grade'),
    )


class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Grade database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating grade tables: {e}")
            raise


class GradeStorageV2:
    """Clean grade storage system"""
    
    def __init__(self, database_url: str):
        self.db_manager = DatabaseManager(database_url)
        self.db_manager.create_tables()
        logger.info("✅ GradeStorageV2 initialized")
    
    def save_grades(self, telegram_id: int, grades_data: List[Dict[str, Any]]) -> bool:
        """Save grades for a user"""
        try:
            with self.db_manager.get_session() as session:
                # Get user ID from telegram_id
                from storage.user_storage_v2 import User
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if not user:
                    logger.error(f"❌ User not found for telegram_id: {telegram_id}")
                    return False
                
                user_id = user.id
                saved_count = 0
                skipped_count = 0
                
                for grade_data in grades_data:
                    # Extract grade information
                    course_name = grade_data.get("name", "")
                    course_code = grade_data.get("code", "")
                    ects = grade_data.get("ects", "")
                    coursework = grade_data.get("coursework", "")
                    final_exam = grade_data.get("final_exam", "")
                    total = grade_data.get("total", "")
                    term_name = grade_data.get("term_name", "")
                    term_id_str = grade_data.get("term_id", "")
                    
                    # Skip if no course name
                    if not course_name:
                        logger.warning(f"⏭️ Skipping grade due to missing course name")
                        skipped_count += 1
                        continue
                    
                    # Handle term
                    term_obj = None
                    if term_id_str:
                        term_obj = session.query(Term).filter_by(term_id=term_id_str).first()
                        if not term_obj:
                            # Create term if not exists
                            term_obj = Term(
                                term_id=term_id_str,
                                name=term_name or term_id_str,
                                is_current=True  # Assume current for now
                            )
                            session.add(term_obj)
                            session.flush()  # Get term_obj.id
                    
                    term_db_id = term_obj.id if term_obj else None
                    
                    # Normalize ECTS
                    try:
                        ects_val = float(ects) if ects else None
                    except Exception:
                        ects_val = None
                    
                    # Extract numeric grade
                    numeric_grade = None
                    if total:
                        match = re.search(r"(\d+)", total)
                        if match:
                            numeric_grade = float(match.group(1))
                    
                    # Determine grade status
                    if not total or "لم يتم النشر" in total:
                        grade_status = "Not Published"
                    elif "%" in total or (numeric_grade is not None):
                        grade_status = "Published"
                    else:
                        grade_status = "Unknown"
                    
                    # Create or update grade
                    existing_grade = session.query(Grade).filter_by(
                        user_id=user_id,
                        course_code=course_code,
                        term_id=term_db_id
                    ).first()
                    
                    if existing_grade:
                        # Update existing grade
                        existing_grade.course_name = course_name
                        existing_grade.ects_credits = ects_val
                        existing_grade.coursework_grade = coursework
                        existing_grade.final_exam_grade = final_exam
                        existing_grade.total_grade_value = total
                        existing_grade.numeric_grade = numeric_grade
                        existing_grade.grade_status = grade_status
                        existing_grade.updated_at = datetime.utcnow()
                    else:
                        # Create new grade
                        grade = Grade(
                            user_id=user_id,
                            term_id=term_db_id,
                            course_name=course_name,
                            course_code=course_code,
                            ects_credits=ects_val,
                            coursework_grade=coursework,
                            final_exam_grade=final_exam,
                            total_grade_value=total,
                            numeric_grade=numeric_grade,
                            grade_status=grade_status,
                        )
                        session.add(grade)
                    
                    saved_count += 1
                
                logger.info(f"✅ Grades saved for user {telegram_id}: {saved_count} saved, {skipped_count} skipped")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error saving grades for user {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error saving grades for user {telegram_id}: {e}")
            return False
    
    def get_user_grades(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Get all grades for a user"""
        try:
            with self.db_manager.get_session() as session:
                from storage.user_storage_v2 import User
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if not user:
                    return []
                
                grades = session.query(Grade).filter_by(user_id=user.id).all()
                return [
                    {
                        "course_name": grade.course_name,
                        "course_code": grade.course_code,
                        "ects_credits": float(grade.ects_credits) if grade.ects_credits else None,
                        "coursework_grade": grade.coursework_grade,
                        "final_exam_grade": grade.final_exam_grade,
                        "total_grade_value": grade.total_grade_value,
                        "numeric_grade": float(grade.numeric_grade) if grade.numeric_grade else None,
                        "grade_status": grade.grade_status,
                        "term_name": grade.term.name if grade.term else None,
                        "created_at": grade.created_at.isoformat() if grade.created_at else None,
                    }
                    for grade in grades
                ]
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error getting grades for user {telegram_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error getting grades for user {telegram_id}: {e}")
            return []
    
    def delete_grades(self, telegram_id: int) -> bool:
        """Delete all grades for a user"""
        try:
            with self.db_manager.get_session() as session:
                from storage.user_storage_v2 import User
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if not user:
                    return False
                
                grades = session.query(Grade).filter_by(user_id=user.id).all()
                for grade in grades:
                    session.delete(grade)
                
                logger.info(f"✅ Deleted {len(grades)} grades for user {telegram_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error deleting grades for user {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting grades for user {telegram_id}: {e}")
            return False
    
    def get_grades(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Compatibility method - alias for get_user_grades"""
        return self.get_user_grades(telegram_id) 