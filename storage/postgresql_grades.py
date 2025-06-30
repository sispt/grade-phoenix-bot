"""
PostgreSQL Grade Storage System
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from storage.models import Base, Grade, DatabaseManager # Import Grade model
# You might not need CONFIG here unless for specific settings
# from config import CONFIG 

logger = logging.getLogger(__name__)

class PostgreSQLGradeStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        # In a real app, migrations handle table creation.
        # Base.metadata.create_all(bind=self.db_manager.engine) # Can be called here if you don't use a separate migrations.py

    def save_grades(self, telegram_id: int, grades_data: List[Dict]):
        try:
            with self.db_manager.get_session() as session:
                # Delete old grades for this user to ensure a clean update
                session.query(Grade).filter_by(telegram_id=telegram_id).delete()
                
                for grade_data_item in grades_data: # Renamed loop variable to avoid confusion
                    # Map incoming dictionary keys to database column names
                    grade = Grade(
                        telegram_id=telegram_id,
                        course_name=grade_data_item.get('name'),
                        course_code=grade_data_item.get('code'),
                        ects_credits=grade_data_item.get('ects'),
                        coursework_grade=grade_data_item.get('coursework'),
                        final_exam_grade=grade_data_item.get('final_exam'),
                        total_grade_value=grade_data_item.get('total'),
                        last_updated=datetime.utcnow()
                    )
                    session.add(grade)
                session.commit()
                logger.info(f"✅ Saved {len(grades_data)} grades for user {telegram_id} to PostgreSQL.")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Error saving grades to PostgreSQL for user {telegram_id}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Unexpected error in save_grades for user {telegram_id}: {e}", exc_info=True)

    def get_grades(self, telegram_id: int) -> List[Dict]:
        try:
            with self.db_manager.get_session() as session:
                grades = session.query(Grade).filter_by(telegram_id=telegram_id).all()
                # Convert Grade objects back to dictionaries for consistency
                return [{
                    'name': g.course_name,
                    'code': g.course_code,
                    'ects': g.ects_credits,
                    'coursework': g.coursework_grade,
                    'final_exam': g.final_exam_grade,
                    'total': g.total_grade_value
                } for g in grades]
        except SQLAlchemyError as e:
            logger.error(f"❌ Error retrieving grades from PostgreSQL for user {telegram_id}: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error in get_grades for user {telegram_id}: {e}", exc_info=True)
            return []

    def get_grades_summary(self) -> Dict[str, Any]:
        """Gets a summary of grades across all users."""
        try:
            with self.db_manager.get_session() as session:
                total_courses = session.query(Grade).count()
                
                # To get recent_updates, you'd need to track when a grade *changed*, not just when it was last fetched.
                # This could be done by comparing the last_updated time of individual grade rows,
                # or by adding a 'grade_last_changed' column to the Grade model.
                # For now, it returns N/A or 0 as a placeholder as per Dashboard needs.
                
                return {
                    "total_courses": total_courses,
                    "recent_updates": 0 # Placeholder: requires more complex logic
                }
        except SQLAlchemyError as e:
            logger.error(f"❌ Error getting grades summary from PostgreSQL: {e}", exc_info=True)
            return {"total_courses": 0, "recent_updates": 0}
        except Exception as e:
            logger.error(f"❌ Unexpected error in get_grades_summary: {e}", exc_info=True)
            return {"total_courses": 0, "recent_updates": 0}