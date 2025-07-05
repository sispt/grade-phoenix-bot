"""
Merged Grade Storage System
Combines file-based and PostgreSQL grade storage
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

from sqlalchemy.exc import SQLAlchemyError

from config import CONFIG
from storage.models import Grade, DatabaseManager, User, Term

logger = logging.getLogger(__name__)


class GradeStorage:
    """File-based grades data storage system"""

    def __init__(self):
        self.data_dir = CONFIG["DATA_DIR"]
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)

    def _get_grades_file(self, telegram_id: int) -> str:
        """Get grades file path for user"""
        return os.path.join(self.data_dir, f"grades_{telegram_id}.json")

    def save_grades(self, telegram_id: int, grades: List[Dict[str, Any]]):
        """Save grades for user"""
        try:
            grades_file = self._get_grades_file(telegram_id)

            grades_data = {
                "telegram_id": telegram_id,
                "grades": grades,
                "last_updated": datetime.now().isoformat(),
                "total_courses": len(grades),
            }

            with open(grades_file, "w", encoding="utf-8") as f:
                json.dump(grades_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Grades saved for user {telegram_id}: {len(grades)} courses")

        except Exception as e:
            logger.error(f"Error saving grades for user {telegram_id}: {e}", exc_info=True)

    def get_grades(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Get grades for user"""
        try:
            grades_file = self._get_grades_file(telegram_id)

            if os.path.exists(grades_file):
                with open(grades_file, "r", encoding="utf-8") as f:
                    grades_data = json.load(f)
                    return grades_data.get("grades", [])
            else:
                return []

        except Exception as e:
            logger.error(f"Error getting grades for user {telegram_id}: {e}", exc_info=True)
            return []

    def delete_grades(self, telegram_id: int) -> bool:
        """Delete grades for user"""
        try:
            grades_file = self._get_grades_file(telegram_id)
            if os.path.exists(grades_file):
                os.remove(grades_file)
                logger.info(f"Grades deleted for user {telegram_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting grades for user {telegram_id}: {e}", exc_info=True)
            return False


class PostgreSQLGradeStorage:
    """PostgreSQL grade storage system"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        logger.warning(f"USING DATABASE_URL: {CONFIG['DATABASE_URL']}")

    def save_grades(self, telegram_id: int, grades_data: List[Dict]):
        try:
            with self.db_manager.get_session() as session:
                # Get user by telegram_id
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if not user:
                    logger.error(f"❌ No user found with telegram_id {telegram_id}")
                    return
                user_id = user.id

                # Delete old grades for this user to ensure a clean update
                session.query(Grade).filter_by(user_id=user_id).delete()

                saved_count = 0
                skipped_count = 0
                for grade_data_item in grades_data:
                    # --- Extract and normalize fields ---
                    name = grade_data_item.get("name")
                    code = grade_data_item.get("code")
                    ects = grade_data_item.get("ects")
                    coursework = grade_data_item.get("coursework")
                    final_exam = grade_data_item.get("final_exam")
                    total = grade_data_item.get("total")
                    term_name = grade_data_item.get("term_name")
                    term_id_str = grade_data_item.get("term_id")

                    # Skip if no course name
                    if not name:
                        logger.warning(
                            f"⏭️ Skipping grade for user {telegram_id} due to missing course name. Raw data: {grade_data_item}"
                        )
                        skipped_count += 1
                        continue

                    # --- Handle term ---
                    term_obj = None
                    if term_id_str:
                        term_obj = session.query(Term).filter_by(term_id=term_id_str).first()
                        if not term_obj:
                            # Create term if not exists
                            term_obj = Term(term_id=term_id_str, name=term_name or term_id_str)
                            session.add(term_obj)
                            session.flush()  # Get term_obj.id
                    term_db_id = term_obj.id if term_obj else None

                    # --- Normalize ECTS ---
                    try:
                        ects_val = float(ects) if ects else None
                    except Exception:
                        ects_val = None

                    # --- Extract numeric grade ---
                    numeric_grade = None
                    if total:
                        import re
                        match = re.search(r"(\d+)", total)
                        if match:
                            numeric_grade = float(match.group(1))

                    # --- Grade status ---
                    if not total or "لم يتم النشر" in total:
                        grade_status = "Not Published"
                    elif "%" in total or (numeric_grade is not None):
                        grade_status = "Published"
                    else:
                        grade_status = "Unknown"

                    # --- Create Grade object ---
                    grade = Grade(
                        user_id=user_id,
                        term_id=term_db_id,
                        course_name=name,
                        course_code=code,
                        ects_credits=ects_val,
                        coursework_grade=coursework,
                        final_exam_grade=final_exam,
                        total_grade_value=total,
                        numeric_grade=numeric_grade,
                        grade_status=grade_status,
                    )
                    session.add(grade)
                    saved_count += 1

                session.commit()
                logger.info(
                    f"✅ Grades saved for user {telegram_id}: {saved_count} courses saved, {skipped_count} skipped"
                )

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error saving grades for user {telegram_id}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Error saving grades for user {telegram_id}: {e}", exc_info=True)

    def get_grades(self, telegram_id: int) -> List[Dict[str, Any]]:
        try:
            with self.db_manager.get_session() as session:
                grades = session.query(Grade).filter_by(telegram_id=telegram_id).all()
                return [
                    {
                        "name": grade.course_name,
                        "code": grade.course_code,
                        "ects": grade.ects_credits,
                        "coursework": grade.coursework_grade,
                        "final_exam": grade.final_exam_grade,
                        "total": grade.total_grade_value,
                    }
                    for grade in grades
                ]
        except SQLAlchemyError as e:
            logger.error(
                f"❌ Database error getting grades for user {telegram_id}: {e}", exc_info=True
            )
            return []
        except Exception as e:
            logger.error(f"❌ Error getting grades for user {telegram_id}: {e}", exc_info=True)
            return []

    def delete_grades(self, telegram_id: int) -> bool:
        try:
            with self.db_manager.get_session() as session:
                deleted_count = (
                    session.query(Grade).filter_by(telegram_id=telegram_id).delete()
                )
                session.commit()
                logger.info(
                    f"✅ Grades deleted for user {telegram_id}: {deleted_count} records"
                )
                return True
        except SQLAlchemyError as e:
            logger.error(
                f"❌ Database error deleting grades for user {telegram_id}: {e}", exc_info=True
            )
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting grades for user {telegram_id}: {e}", exc_info=True)
            return False
