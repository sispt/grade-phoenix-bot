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
        """Save grades for a user (by telegram_id) using only fields present in the SQL schema."""
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
                    name = grade_data.get("name", "")
                    code = grade_data.get("code", "")
                    ects = grade_data.get("ects", None)
                    coursework = grade_data.get("coursework", None)
                    final_exam = grade_data.get("final_exam", None)
                    total = grade_data.get("total", None)
                    grade_status = grade_data.get("grade_status", "Unknown")
                    numeric_grade = grade_data.get("numeric_grade", None)
                    # Skip if no course name
                    if not name:
                        logger.warning(f"⏭️ Skipping grade due to missing course name")
                        skipped_count += 1
                        continue
                    # Normalize ECTS
                    try:
                        ects_val = float(ects) if ects is not None and ects != '' else None
                    except Exception:
                        ects_val = None
                    # Normalize numeric_grade
                    try:
                        numeric_grade_val = float(numeric_grade) if numeric_grade is not None and numeric_grade != '' else None
                    except Exception:
                        numeric_grade_val = None
                    # Determine grade status if not provided
                    if not total or (isinstance(total, str) and "لم يتم النشر" in total):
                        grade_status = "Not Published"
                    elif (isinstance(total, str) and "%" in total) or (numeric_grade_val is not None):
                        grade_status = "Published"
                    else:
                        grade_status = "Unknown"
                    # Create or update grade
                    existing_grade = session.query(Grade).filter_by(
                        telegram_id=telegram_id,
                        code=code
                    ).first()
                    logger.debug(f"[DEBUG] Existing grade for telegram_id={telegram_id}, code={code}: {existing_grade}")
                    if existing_grade:
                        existing_grade.name = name
                        existing_grade.code = code
                        setattr(existing_grade, 'ects', Decimal(str(ects_val)) if ects_val is not None else None)
                        setattr(existing_grade, 'coursework', str(coursework) if coursework is not None else None)
                        setattr(existing_grade, 'final_exam', str(final_exam) if final_exam is not None else None)
                        setattr(existing_grade, 'total', str(total) if total is not None else None)
                        setattr(existing_grade, 'numeric_grade', Decimal(str(numeric_grade_val)) if numeric_grade_val is not None else None)
                        setattr(existing_grade, 'grade_status', str(grade_status))
                        setattr(existing_grade, 'updated_at', datetime.now(timezone.utc))
                        logger.debug(f"[DEBUG] Updated existing grade: {existing_grade}")
                    else:
                        grade = Grade(
                            telegram_id=telegram_id,
                            name=name,
                            code=code,
                            ects=Decimal(str(ects_val)) if ects_val is not None else None,
                            coursework=str(coursework) if coursework is not None else None,
                            final_exam=str(final_exam) if final_exam is not None else None,
                            total=str(total) if total is not None else None,
                            numeric_grade=Decimal(str(numeric_grade_val)) if numeric_grade_val is not None else None,
                            grade_status=str(grade_status),
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        )
                        session.add(grade)
                        logger.debug(f"[DEBUG] Added new grade: {grade}")
                    saved_count += 1
                logger.info(f"✅ Grades saved for user {telegram_id}: {saved_count} saved, {skipped_count} skipped")
                logger.debug(f"[DEBUG] Committing session for telegram_id={telegram_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error saving grades for user {telegram_id}: {e}", exc_info=True)
            return False
        except Exception as e:
            import traceback
            logger.error(f"❌ Error saving grades for user {telegram_id}: {e}\n{traceback.format_exc()}")
            return False
    def get_user_grades(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Get all grades for a user (by telegram_id) using unified API terminology"""
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