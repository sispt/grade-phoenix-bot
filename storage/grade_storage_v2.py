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
    """Clean grade storage system (grades are associated by user_id, not telegram_id)"""
    
    def __init__(self, database_url: str):
        self.db_manager = DatabaseManager(database_url)
        self.db_manager.create_all_tables()
        logger.info("✅ GradeStorageV2 initialized")
    
    def save_grades(self, telegram_id: int, grades_data: List[Dict[str, Any]]) -> bool:
        """Save grades for a user (by telegram_id)"""
        try:
            logger.debug(f"[DEBUG] save_grades called for telegram_id={telegram_id} with {len(grades_data)} grades.")
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                logger.debug(f"[DEBUG] User lookup for telegram_id={telegram_id}: {user}")
                if not user:
                    logger.error(f"❌ User not found for telegram_id: {telegram_id}")
                    return False
                saved_count = 0
                skipped_count = 0
                for grade_data in grades_data:
                    logger.debug(f"[DEBUG] Processing grade_data: {grade_data}")
                    course_name = grade_data.get("name", "")
                    course_code = grade_data.get("code", "")
                    ects = grade_data.get("ects", "")
                    coursework = grade_data.get("coursework", "")
                    final_exam = grade_data.get("final_exam", "")
                    total = grade_data.get("total", "")
                    # Skip if no course name
                    if not course_name:
                        logger.warning(f"⏭️ Skipping grade due to missing course name")
                        skipped_count += 1
                        continue
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
                        course_code=course_code
                    ).first()
                    logger.debug(f"[DEBUG] Existing grade for telegram_id={telegram_id}, course_code={course_code}: {existing_grade}")
                    if existing_grade:
                        existing_grade.course_name = course_name
                        existing_grade.course_code = course_code
                        setattr(existing_grade, 'ects_credits', ects_val if ects_val is not None else None)
                        existing_grade.coursework_grade = coursework
                        existing_grade.final_exam_grade = final_exam
                        existing_grade.total_grade_value = total
                        setattr(existing_grade, 'numeric_grade', Decimal(str(numeric_grade)) if numeric_grade is not None else None)
                        setattr(existing_grade, 'grade_status', grade_status)
                        setattr(existing_grade, 'updated_at', datetime.now(timezone.utc))
                        logger.debug(f"[DEBUG] Updated existing grade: {existing_grade}")
                    else:
                        grade = Grade(
                            telegram_id=telegram_id,
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
                        logger.debug(f"[DEBUG] Added new grade: {grade}")
                    saved_count += 1
                logger.info(f"✅ Grades saved for user {telegram_id}: {saved_count} saved, {skipped_count} skipped")
                logger.debug(f"[DEBUG] Committing session for telegram_id={telegram_id}")
                # The commit is handled by the context manager
                return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error saving grades for user {telegram_id}: {e}", exc_info=True)
            return False
        except Exception as e:
            import traceback
            logger.error(f"❌ Error saving grades for user {telegram_id}: {e}\n{traceback.format_exc()}")
            return False
    def get_user_grades(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Get all grades for a user (by telegram_id)"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if not user:
                    logger.error(f"❌ User not found for telegram_id: {telegram_id}")
                    return []
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
        """Delete all grades for a user (by telegram_id)"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if not user:
                    logger.error(f"❌ User not found for telegram_id: {telegram_id}")
                    return False
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