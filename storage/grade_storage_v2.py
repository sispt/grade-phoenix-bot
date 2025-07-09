"""
Grade Storage System v2
Handles grade data storage and comparison using PostgreSQL
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import logging
import re
import time
from sqlalchemy.exc import OperationalError

RETRY_ATTEMPTS = 3
RETRY_SLEEP = 2  # seconds

from .models import DatabaseManager, Grade, User

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
                # Get existing grades for this user
                existing_grades = session.query(Grade).filter(Grade.username == username).all()
                existing_grades_dict = {grade.code: grade for grade in existing_grades}
                
                changes = []
                
                for grade_data in grades_data:
                    course_code = grade_data.get('code')
                    if not course_code:
                        continue
                    
                    # Extract numeric grade if possible
                    numeric_grade = self._extract_numeric_grade(grade_data.get('total', ''))
                    
                    if course_code in existing_grades_dict:
                        # Update existing grade
                        existing_grade = existing_grades_dict[course_code]
                        changes.extend(self._update_grade_if_changed(existing_grade, grade_data, numeric_grade))
                    else:
                        # Create new grade
                        new_grade = Grade(
                            username=username,
                            name=grade_data.get('name', ''),
                            code=course_code,
                            coursework=grade_data.get('coursework'),
                            final_exam=grade_data.get('final_exam'),
                            total=grade_data.get('total'),
                            ects=grade_data.get('ects'),
                            term_name=grade_data.get('term_name'),
                            term_id=grade_data.get('term_id'),
                            grade_status=grade_data.get('grade_status', 'Unknown'),
                            numeric_grade=numeric_grade
                        )
                        session.add(new_grade)
                        changes.append(f"New grade added: {grade_data.get('name')} ({course_code})")
                
                session.commit()
                
                if changes:
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
                # Get the most recent term
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
                # Get current term
                current_term = session.query(Grade.term_name).filter(
                    Grade.username == username
                ).order_by(desc(Grade.updated_at)).first()
                
                if not current_term:
                    return []
                
                # Get all terms except current
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
    
    def compare_grades(self, username: str, new_grades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compare new grades with stored grades and return changes"""
        def _inner():
            with self._get_session() as session:
                # Get existing grades
                existing_grades = session.query(Grade).filter(Grade.username == username).all()
                existing_dict = {grade.code: grade for grade in existing_grades}
                
                changes = []
                
                for new_grade in new_grades:
                    course_code = new_grade.get('code')
                    if not course_code:
                        continue
                    
                    if course_code in existing_dict:
                        existing = existing_dict[course_code]
                        change = self._detect_grade_change(existing, new_grade)
                        if change:
                            changes.append(change)
                    else:
                        # New grade
                        changes.append({
                            'course_name': new_grade.get('name', ''),
                            'course_code': course_code,
                            'type': 'new_grade',
                            'old_value': None,
                            'new_value': new_grade.get('total'),
                            'field': 'total'
                        })
                
                return changes
        try:
            return self._retry_db(_inner)
        except Exception as e:
            logger.error(f"❌ Failed to compare grades: {e}")
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
    
    def _update_grade_if_changed(self, existing_grade: Grade, new_data: Dict[str, Any], numeric_grade: Optional[float]) -> List[str]:
        """Update grade if there are changes and return list of changes"""
        changes = []
        
        # Check each field for changes
        fields_to_check = ['name', 'coursework', 'final_exam', 'total', 'ects', 'term_name', 'term_id', 'grade_status']
        
        for field in fields_to_check:
            old_value = getattr(existing_grade, field)
            new_value = new_data.get(field)
            
            if old_value != new_value:
                setattr(existing_grade, field, new_value)
                changes.append(f"{field} changed: {old_value} → {new_value}")
        
        # Update numeric grade
        if existing_grade.numeric_grade != numeric_grade:
            existing_grade.numeric_grade = numeric_grade
            changes.append(f"numeric_grade changed: {existing_grade.numeric_grade} → {numeric_grade}")
        
        # Update timestamp
        existing_grade.updated_at = datetime.now(timezone.utc)
        
        return changes
    
    def _detect_grade_change(self, existing_grade: Grade, new_grade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect changes between existing and new grade"""
        changes = []
        
        fields_to_check = ['coursework', 'final_exam', 'total']
        
        for field in fields_to_check:
            old_value = getattr(existing_grade, field)
            new_value = new_grade.get(field)
            
            if old_value != new_value:
                changes.append({
                    'course_name': existing_grade.name,
                    'course_code': existing_grade.code,
                    'type': 'grade_change',
                    'old_value': old_value,
                    'new_value': new_value,
                    'field': field
                })
        
        return changes[0] if changes else None
    
    def _extract_numeric_grade(self, grade_text: str) -> Optional[float]:
        """Extract numeric grade from grade text"""
        if not grade_text or grade_text == 'لم يتم النشر':
            return None
        
        try:
            # Try to extract number from text like "85 %" or "90"
            match = re.search(r'(\d+(?:\.\d+)?)', str(grade_text))
            if match:
                return float(match.group(1))
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _grade_to_dict(self, grade: Grade) -> Dict[str, Any]:
        """Convert Grade object to dictionary"""
        return {
            'id': grade.id,
            'username': grade.username,
            'name': grade.name,
            'code': grade.code,
            'coursework': grade.coursework,
            'final_exam': grade.final_exam,
            'total': grade.total,
            'ects': grade.ects,
            'term_name': grade.term_name,
            'term_id': grade.term_id,
            'grade_status': grade.grade_status,
            'numeric_grade': grade.numeric_grade,
            'created_at': grade.created_at.isoformat() if grade.created_at else None,
            'updated_at': grade.updated_at.isoformat() if grade.updated_at else None
        } 