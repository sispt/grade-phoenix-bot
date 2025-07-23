"""
Grade Storage System v2
Handles grade data storage and comparison using PostgreSQL
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging
import re
import time
from sqlalchemy.exc import OperationalError

RETRY_ATTEMPTS = 3
RETRY_SLEEP = 2  # seconds

from .models import DatabaseManager, Grade

logger = logging.getLogger(__name__)

class GradeStorageV2:
    """Grade storage system using PostgreSQL"""
    
    def __init__(self, database_url: str):
        self.db_manager = DatabaseManager(database_url)
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure database tables exist"""
        try:
            self.db_manager.create_tables()
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def _get_session(self) -> Session:
        """Get database session"""
        return self.db_manager.get_session()
    
    def _retry_db(self, func, *args, **kwargs):
        last_exc = None
        for attempt in range(RETRY_ATTEMPTS):
            try:
                return func(*args, **kwargs)
            except OperationalError as e:
                last_exc = e
                logger.warning(f"[Retry] DB operation failed (attempt {attempt+1}/{RETRY_ATTEMPTS}): {e}")
                time.sleep(RETRY_SLEEP)
        logger.error(f"[Persistent DB Error] Operation failed after {RETRY_ATTEMPTS} attempts: {last_exc}")
        if last_exc is not None:
            raise last_exc
        else:
            raise Exception("Unknown persistent DB error after retries.")

    def store_grades(self, username: str, grades_data: List[Dict[str, Any]]) -> bool:
        """Store or update grades for a user"""
        def _inner():
            with self._get_session() as session:
                # Deduplicate grades_data by course code, keep last occurrence
                unique_grades = {}
                for grade_data in grades_data:
                    course_code = grade_data.get('code')
                    if course_code:
                        unique_grades[course_code] = grade_data
                grades_data = list(unique_grades.values())

                # Get existing grades for this user
                existing_grades = session.query(Grade).filter(Grade.username == username).all()
                existing_grades_dict = {
                    (grade.code, grade.term_id): grade for grade in existing_grades
                }

                changes = []
                
                for grade_data in grades_data:
                    course_code = grade_data.get('code')
                    if not course_code:
                        continue
                    
                    numeric_grade = self._extract_numeric_grade(grade_data.get('total', ''))
                    term_id = grade_data.get('term_id')
                    key = (course_code, term_id)

                    if key in existing_grades_dict:
                        # Update existing grade if changed
                        existing_grade = existing_grades_dict[key]
                        changes.extend(self._update_grade_if_changed(existing_grade, grade_data, numeric_grade))
                    else:
                        # Create new grade entry
                        new_grade = Grade(
                            username=username,
                            name=grade_data.get('name', ''),
                            code=course_code,
                            coursework=grade_data.get('coursework'),
                            final_exam=grade_data.get('final_exam'),
                            total=grade_data.get('total'),
                            ects=grade_data.get('ects'),
                            term_name=grade_data.get('term_name'),
                            term_id=term_id,
                            grade_status=grade_data.get('grade_status', 'Unknown'),
                            numeric_grade=numeric_grade,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc)
                        )
                        session.add(new_grade)
                        changes.append(f"New grade added: {grade_data.get('name')} ({course_code} - {term_id})")

                if changes:
                    session.commit()
                    logger.info(f"✅ Grades updated for {username}: {len(changes)} changes")
                    for change in changes:
                        logger.debug(f"  - {change}")
                else:
                    logger.info(f"✅ No grade changes for {username}")
                
                return True
        try:
            return self._retry_db(_inner)
        except Exception as e:
            logger.error(f"❌ Failed to store grades: {e}")
            return False
    
    def get_user_grades(self, username: str, term_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get grades for a user, optionally filtered by term"""
        def _inner():
            with self._get_session() as session:
                query = session.query(Grade).filter(Grade.username == username)
                if term_name:
                    query = query.filter(Grade.term_name == term_name)
                grades = query.order_by(Grade.name).all()
                return [self._grade_to_dict(grade) for grade in grades]
        try:
            return self._retry_db(_inner)
        except Exception as e:
            logger.error(f"❌ Failed to get user grades: {e}")
            return []
    
    def get_current_term_grades(self, username: str) -> List[Dict[str, Any]]:
        """Get current term grades for a user"""
        def _inner():
            with self._get_session() as session:
                latest_term = session.query(Grade.term_name).filter(
                    Grade.username == username
                ).order_by(desc(Grade.updated_at)).first()
                if latest_term:
                    return self.get_user_grades(username, latest_term[0])
                return []
        try:
            return self._retry_db(_inner)
        except Exception as e:
            logger.error(f"❌ Failed to get current term grades: {e}")
            return []
    
    def get_old_term_grades(self, username: str) -> List[Dict[str, Any]]:
        """Get old term grades for a user (excluding current term)"""
        def _inner():
            with self._get_session() as session:
                current_term = session.query(Grade.term_name).filter(
                    Grade.username == username
                ).order_by(desc(Grade.updated_at)).first()
                if not current_term:
                    return []
                grades = session.query(Grade).filter(
                    and_(
                        Grade.username == username,
                        Grade.term_name != current_term[0]
                    )
                ).order_by(desc(Grade.term_name), Grade.name).all()
                return [self._grade_to_dict(grade) for grade in grades]
        try:
            return self._retry_db(_inner)
        except Exception as e:
            logger.error(f"❌ Failed to get old term grades: {e}")
            return []
    
    def get_grade_history(self, username: str, course_code: str) -> List[Dict[str, Any]]:
        """Get grade history for a specific course"""
        def _inner():
            with self._get_session() as session:
                grades = session.query(Grade).filter(
                    and_(
                        Grade.username == username,
                        Grade.code == course_code
                    )
                ).order_by(desc(Grade.updated_at)).all()
                return [self._grade_to_dict(grade) for grade in grades]
        try:
            return self._retry_db(_inner)
        except Exception as e:
            logger.error(f"❌ Failed to get grade history: {e}")
            return []
    
    def delete_user_grades(self, username: str) -> bool:
        """Delete all grades for a user"""
        def _inner():
            with self._get_session() as session:
                grades = session.query(Grade).filter(Grade.username == username).all()
                for grade in grades:
                    session.delete(grade)
                session.commit()
                logger.info(f"✅ Deleted all grades for user: {username}")
                return True
        try:
            return self._retry_db(_inner)
        except Exception as e:
            logger.error(f"❌ Failed to delete user grades: {e}")
            return False
    
    def get_grade_statistics(self, username: str) -> Dict[str, Any]:
        """Get grade statistics for a user"""
        def _inner():
            with self._get_session() as session:
                grades = session.query(Grade).filter(Grade.username == username).all()
                total_courses = len(grades)
                published_grades = [g for g in grades if g.total and g.total != 'لم يتم النشر']
                numeric_grades = [g.numeric_grade for g in published_grades if g.numeric_grade is not None]
                
                stats = {
                    'total_courses': total_courses,
                    'published_courses': len(published_grades),
                    'unpublished_courses': total_courses - len(published_grades),
                    'average_grade': sum(numeric_grades) / len(numeric_grades) if numeric_grades else 0,
                    'highest_grade': max(numeric_grades) if numeric_grades else 0,
                    'lowest_grade': min(numeric_grades) if numeric_grades else 0,
                    'total_ects': sum(g.ects for g in grades if g.ects),
                    'terms': list(set(g.term_name for g in grades if g.term_name))
                }
                return stats
        try:
            return self._retry_db(_inner)
        except Exception as e:
            logger.error(f"❌ Failed to get grade statistics: {e}")
            return {}
    
    def _update_grade_if_changed(
        self,
        existing_grade: Grade,
        new_data: Dict[str, Any],
        numeric_grade: Optional[float]
    ) -> List[str]:
        """Update grade if there are changes and return list of changes"""
        def _normalize(val):
            if val is None:
                return None
            return str(val).strip()

        changes = []
        fields_to_check = ['name', 'coursework', 'final_exam', 'total', 'ects', 'term_name', 'term_id', 'grade_status']

        for field in fields_to_check:
            old_value = _normalize(getattr(existing_grade, field))
            new_value = _normalize(new_data.get(field))
            if old_value != new_value:
                changes.append(f"{field} changed from {old_value} to {new_value}")
                setattr(existing_grade, field, new_value)

        if existing_grade.numeric_grade != numeric_grade:
            changes.append(f"numeric_grade changed from {existing_grade.numeric_grade} to {numeric_grade}")
            existing_grade.numeric_grade = numeric_grade

        if changes:
            existing_grade.updated_at = datetime.now(timezone.utc)
            logger.debug(f"Updating grade {existing_grade.code} for user {existing_grade.username} with changes: {changes}")

        return changes

    def _grade_to_dict(self, grade: Grade) -> Dict[str, Any]:
        """Convert Grade ORM object to dict"""
        return {
            "id": grade.id,
            "username": grade.username,
            "name": grade.name,
            "code": grade.code,
            "coursework": grade.coursework,
            "final_exam": grade.final_exam,
            "total": grade.total,
            "ects": grade.ects,
            "term_name": grade.term_name,
            "term_id": grade.term_id,
            "grade_status": grade.grade_status,
            "numeric_grade": grade.numeric_grade,
            "created_at": grade.created_at.isoformat() if grade.created_at else None,
            "updated_at": grade.updated_at.isoformat() if grade.updated_at else None
        }
    
    def _extract_numeric_grade(self, grade_str: str) -> Optional[float]:
        """Extract numeric grade from string"""
        if not grade_str:
            return None
        try:
            # Extract digits and decimal point
            match = re.search(r"(\d+(\.\d+)?)", grade_str)
            if match:
                return float(match.group(1))
        except Exception as e:
            logger.warning(f"Could not extract numeric grade from '{grade_str}': {e}")
        return None
