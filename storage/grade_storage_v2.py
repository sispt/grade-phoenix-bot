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
from storage.models import DatabaseManager, Grade

logger = logging.getLogger(__name__)


class GradeStorageV2:
    """Production-ready grade storage using the standard Grade table."""
    def __init__(self, database_url: str):
        self.db_manager = DatabaseManager(database_url)
        self.db_manager.create_all_tables()
        logger.info("✅ GradeStorageV2 (standard) initialized")

    def save_grades(self, username_unique: str, grades_data, notify_callback=None) -> bool:
        try:
            logger.info(f"[CALL] save_grades (standard) for username_unique={username_unique} with {len(grades_data)} grades.")
            with self.db_manager.get_session() as session:
                # Remove old grades for this user
                session.query(Grade).filter_by(username_unique=username_unique).delete()
                # Add new grades
                for grade_data in grades_data:
                    grade = Grade(
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
            return True
        except Exception as e:
            logger.error(f"❌ Error saving grades for user {username_unique}: {e}")
            return False

    def get_user_grades(self, username_unique: str):
        try:
            logger.info(f"[CALL] get_user_grades (standard) for username_unique={username_unique}")
            with self.db_manager.get_session() as session:
                grades = session.query(Grade).filter_by(username_unique=username_unique).all()
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
        except Exception as e:
            logger.error(f"❌ Error getting grades for user {username_unique}: {e}")
            return []

    def delete_grades(self, username_unique: str) -> bool:
        try:
            logger.info(f"[CALL] delete_grades (standard) for username_unique={username_unique}")
            with self.db_manager.get_session() as session:
                session.query(Grade).filter_by(username_unique=username_unique).delete()
                session.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting grades for user {username_unique}: {e}")
            return False


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