"""
📊 PostgreSQL Grades Storage System
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from config import CONFIG
from storage.models import DatabaseManager, Grade

logger = logging.getLogger(__name__)

class PostgreSQLGradeStorage:
    """PostgreSQL-based grades data storage system"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db_manager = database_manager
    
    def save_grades(self, telegram_id: int, grades: List[Dict[str, Any]]):
        """Save grades for user"""
        try:
            with self.db_manager.get_session() as session:
                # Delete existing grades for this user
                session.query(Grade).filter(Grade.telegram_id == telegram_id).delete()
                
                # Add new grades
                for grade_data in grades:
                    grade = Grade(
                        telegram_id=telegram_id,
                        course_name=grade_data.get("المقرر", "غير محدد"),
                        course_code=grade_data.get("كود المادة", ""),
                        ects_credits=grade_data.get("رصيد ECTS", ""),
                        practical_grade=grade_data.get("درجة الأعمال", "لم يتم النشر"),
                        theoretical_grade=grade_data.get("درجة النظري", "لم يتم النشر"),
                        final_grade=grade_data.get("الدرجة", "لم يتم النشر"),
                        last_updated=datetime.utcnow()
                    )
                    session.add(grade)
                
                session.commit()
                logger.info(f"Grades saved for user {telegram_id}: {len(grades)} courses")
                
        except SQLAlchemyError as e:
            logger.error(f"Database error saving grades for user {telegram_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saving grades for user {telegram_id}: {e}")
            raise
    
    def get_grades(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Get grades for user"""
        try:
            with self.db_manager.get_session() as session:
                grades = session.query(Grade).filter(Grade.telegram_id == telegram_id).all()
                return [grade.to_dict() for grade in grades]
        except SQLAlchemyError as e:
            logger.error(f"Database error loading grades for user {telegram_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading grades for user {telegram_id}: {e}")
            return []
    
    def get_grades_data(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get complete grades data for user"""
        try:
            with self.db_manager.get_session() as session:
                grades = session.query(Grade).filter(Grade.telegram_id == telegram_id).all()
                
                if grades:
                    return {
                        "telegram_id": telegram_id,
                        "grades": [grade.to_dict() for grade in grades],
                        "last_updated": grades[0].last_updated.isoformat() if grades[0].last_updated else None,
                        "total_courses": len(grades)
                    }
                else:
                    return None
                    
        except SQLAlchemyError as e:
            logger.error(f"Database error loading grades data for user {telegram_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading grades data for user {telegram_id}: {e}")
            return None
    
    def get_last_updated(self, telegram_id: int) -> Optional[str]:
        """Get last update time for user grades"""
        try:
            with self.db_manager.get_session() as session:
                grade = session.query(Grade).filter(Grade.telegram_id == telegram_id).first()
                return grade.last_updated.isoformat() if grade and grade.last_updated else None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting last updated for user {telegram_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting last updated for user {telegram_id}: {e}")
            return None
    
    def get_total_courses(self, telegram_id: int) -> int:
        """Get total courses count for user"""
        try:
            with self.db_manager.get_session() as session:
                return session.query(Grade).filter(Grade.telegram_id == telegram_id).count()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting total courses for user {telegram_id}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error getting total courses for user {telegram_id}: {e}")
            return 0
    
    def delete_grades(self, telegram_id: int) -> bool:
        """Delete grades for user"""
        try:
            with self.db_manager.get_session() as session:
                deleted_count = session.query(Grade).filter(Grade.telegram_id == telegram_id).delete()
                session.commit()
                logger.info(f"Grades deleted for user {telegram_id}: {deleted_count} courses")
                return deleted_count > 0
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting grades for user {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting grades for user {telegram_id}: {e}")
            return False
    
    def get_all_grades_data(self) -> List[Dict[str, Any]]:
        """Get all grades data"""
        try:
            with self.db_manager.get_session() as session:
                # Get all grades grouped by telegram_id
                grades_by_user = {}
                
                grades = session.query(Grade).all()
                for grade in grades:
                    telegram_id = grade.telegram_id
                    if telegram_id not in grades_by_user:
                        grades_by_user[telegram_id] = {
                            "telegram_id": telegram_id,
                            "grades": [],
                            "last_updated": None,
                            "total_courses": 0
                        }
                    
                    grades_by_user[telegram_id]["grades"].append(grade.to_dict())
                    if grade.last_updated:
                        grades_by_user[telegram_id]["last_updated"] = grade.last_updated.isoformat()
                
                # Update total_courses for each user
                for user_data in grades_by_user.values():
                    user_data["total_courses"] = len(user_data["grades"])
                
                return list(grades_by_user.values())
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all grades data: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting all grades data: {e}")
            return []
    
    def get_grades_summary(self) -> Dict[str, Any]:
        """Get summary of all grades"""
        try:
            with self.db_manager.get_session() as session:
                total_users = session.query(Grade.telegram_id).distinct().count()
                total_courses = session.query(Grade).count()
                
                # Get recent updates (last 24 hours)
                yesterday = datetime.utcnow() - datetime.timedelta(days=1)
                recent_updates = session.query(Grade.telegram_id).filter(
                    Grade.last_updated >= yesterday
                ).distinct().count()
                
                return {
                    "total_users": total_users,
                    "total_courses": total_courses,
                    "recent_updates": recent_updates,
                    "last_backup": datetime.utcnow().isoformat()
                }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting grades summary: {e}")
            return {
                "total_users": 0,
                "total_courses": 0,
                "recent_updates": 0,
                "last_backup": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting grades summary: {e}")
            return {
                "total_users": 0,
                "total_courses": 0,
                "recent_updates": 0,
                "last_backup": datetime.utcnow().isoformat()
            }
    
    def get_course_statistics(self) -> Dict[str, Any]:
        """Get statistics about courses"""
        try:
            with self.db_manager.get_session() as session:
                # Get unique course names
                course_names = session.query(Grade.course_name).distinct().all()
                course_names = [name[0] for name in course_names if name[0] and name[0] != "غير محدد"]
                
                # Get average grades (where available)
                grades_with_final = session.query(Grade).filter(
                    Grade.final_grade.isnot(None),
                    Grade.final_grade != "لم يتم النشر"
                ).all()
                
                total_final_grades = 0
                valid_grades_count = 0
                
                for grade in grades_with_final:
                    try:
                        grade_value = float(grade.final_grade)
                        total_final_grades += grade_value
                        valid_grades_count += 1
                    except (ValueError, TypeError):
                        continue
                
                avg_grade = total_final_grades / valid_grades_count if valid_grades_count > 0 else 0
                
                return {
                    "unique_courses": len(course_names),
                    "course_names": course_names,
                    "total_grades": len(grades_with_final),
                    "valid_grades": valid_grades_count,
                    "average_grade": round(avg_grade, 2)
                }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting course statistics: {e}")
            return {
                "unique_courses": 0,
                "course_names": [],
                "total_grades": 0,
                "valid_grades": 0,
                "average_grade": 0
            }
        except Exception as e:
            logger.error(f"Error getting course statistics: {e}")
            return {
                "unique_courses": 0,
                "course_names": [],
                "total_grades": 0,
                "valid_grades": 0,
                "average_grade": 0
            } 