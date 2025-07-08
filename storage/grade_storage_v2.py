"""
📊 Grade Storage V2 - Clean Implementation
Handles grade data storage with PostgreSQL
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from decimal import Decimal
import re

from sqlalchemy.exc import SQLAlchemyError

# Import models from the main models file
from storage.models import Base, User, Term, Grade, DatabaseManager

logger = logging.getLogger(__name__)


class GradeStorageV2:
    """Clean grade storage system"""
    
    def __init__(self, database_url: str):
        self.db_manager = DatabaseManager(database_url)
        self.db_manager.create_all_tables()
        logger.info("✅ GradeStorageV2 initialized")
    
    def save_grades(self, telegram_id: int, grades_data: List[Dict[str, Any]]) -> bool:
        """Save grades for a user"""
        try:
            with self.db_manager.get_session() as session:
                # Get user by telegram_id (no need for user_id)
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if not user:
                    logger.error(f"❌ User not found for telegram_id: {telegram_id}")
                    return False
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
                        telegram_id=telegram_id,
                        code=course_code,
                        term_id=term_db_id
                    ).first()
                    if existing_grade:
                        # Update existing grade
                        existing_grade.course_name = course_name
                        existing_grade.course_code = course_code
                        # Fix: assign to instance attributes, not class variables
                        setattr(existing_grade, 'ects_credits', ects_val if ects_val is not None else None)
                        existing_grade.coursework_grade = coursework
                        existing_grade.final_exam_grade = final_exam
                        existing_grade.total_grade_value = total
                        setattr(existing_grade, 'numeric_grade', Decimal(str(numeric_grade)) if numeric_grade is not None else None)
                        setattr(existing_grade, 'grade_status', grade_status)
                        setattr(existing_grade, 'updated_at', datetime.now(timezone.utc))
                    else:
                        # Create new grade
                        grade = Grade(
                            telegram_id=telegram_id,
                            term_id=term_db_id,
                            course_name=course_name,
                            course_code=course_code,
                            ects_credits=ects_val if ects_val is not None else None,
                            coursework_grade=coursework,
                            final_exam_grade=final_exam,
                            total_grade_value=total,
                            numeric_grade=Decimal(str(numeric_grade)) if numeric_grade is not None else None,
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
                grades = session.query(Grade).filter_by(telegram_id=telegram_id).all()
                return [
                    {
                        "name": grade.course_name,
                        "code": grade.course_code,
                        "ects": safe_float(getattr(grade, 'ects_credits', None)),
                        "coursework": grade.coursework_grade,
                        "final_exam": grade.final_exam_grade,
                        "total": grade.total_grade_value,
                        "numeric_grade": safe_float(getattr(grade, 'numeric_grade', None)),
                        "grade_status": grade.grade_status,
                        "term_name": grade.term.name if getattr(grade, 'term', None) and getattr(grade.term, 'name', None) else None,
                        "created_at": grade.created_at.isoformat() if getattr(grade, 'created_at', None) else None,
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
                grades = session.query(Grade).filter_by(telegram_id=telegram_id).all()
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

def safe_float(val):
    from sqlalchemy.orm.attributes import InstrumentedAttribute
    if val is None:
        return None
    if hasattr(val, '__class__') and val.__class__.__name__ == 'InstrumentedAttribute':
        return None
    try:
        return float(val)
    except Exception:
        return None 