"""
📊 Grade Storage System

Handles grade data storage and retrieval.
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from config import CONFIG

logger = logging.getLogger(__name__)

class GradeStorage:
    """Grades data storage system"""
    
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
                "total_courses": len(grades)
            }
            
            with open(grades_file, 'w', encoding='utf-8') as f:
                json.dump(grades_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Grades saved for user {telegram_id}: {len(grades)} courses")
            
        except Exception as e:
            logger.error(f"Error saving grades for user {telegram_id}: {e}")
    
    def get_grades(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Get grades for user"""
        try:
            grades_file = self._get_grades_file(telegram_id)
            
            if os.path.exists(grades_file):
                with open(grades_file, 'r', encoding='utf-8') as f:
                    grades_data = json.load(f)
                    return grades_data.get("grades", [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error loading grades for user {telegram_id}: {e}")
            return []
    
    def get_grades_data(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get complete grades data for user"""
        try:
            grades_file = self._get_grades_file(telegram_id)
            
            if os.path.exists(grades_file):
                with open(grades_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error loading grades data for user {telegram_id}: {e}")
            return None
    
    def get_last_updated(self, telegram_id: int) -> Optional[str]:
        """Get last update time for user grades"""
        grades_data = self.get_grades_data(telegram_id)
        if grades_data:
            return grades_data.get("last_updated")
        return None
    
    def get_total_courses(self, telegram_id: int) -> int:
        """Get total courses count for user"""
        grades_data = self.get_grades_data(telegram_id)
        if grades_data:
            return grades_data.get("total_courses", 0)
        return 0
    
    def delete_grades(self, telegram_id: int) -> bool:
        """Delete grades for user"""
        try:
            grades_file = self._get_grades_file(telegram_id)
            
            if os.path.exists(grades_file):
                os.remove(grades_file)
                logger.info(f"Grades deleted for user {telegram_id}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error deleting grades for user {telegram_id}: {e}")
            return False
    
    def get_all_grades_files(self) -> List[str]:
        """Get all grades files"""
        try:
            grades_files = []
            for filename in os.listdir(self.data_dir):
                if filename.startswith("grades_") and filename.endswith(".json"):
                    grades_files.append(os.path.join(self.data_dir, filename))
            return grades_files
        except Exception as e:
            logger.error(f"Error getting grades files: {e}")
            return []
    
    def get_all_grades_data(self) -> List[Dict[str, Any]]:
        """Get all grades data"""
        try:
            all_grades = []
            grades_files = self.get_all_grades_files()
            
            for grades_file in grades_files:
                try:
                    with open(grades_file, 'r', encoding='utf-8') as f:
                        grades_data = json.load(f)
                        all_grades.append(grades_data)
                except Exception as e:
                    logger.error(f"Error loading grades file {grades_file}: {e}")
            
            return all_grades
            
        except Exception as e:
            logger.error(f"Error getting all grades data: {e}")
            return []
    
    def backup_grades(self) -> str:
        """Create backup of all grades data"""
        try:
            backup_file = os.path.join(
                CONFIG.get("BACKUP_DIR", "backups"),
                f"grades_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            os.makedirs(os.path.dirname(backup_file), exist_ok=True)
            
            all_grades = self.get_all_grades_data()
            
            backup_data = {
                "backup_date": datetime.now().isoformat(),
                "total_users": len(all_grades),
                "grades_data": all_grades
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Grades backup created: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Error creating grades backup: {e}")
            return ""
    
    def get_grades_summary(self) -> Dict[str, Any]:
        """Get summary of all grades"""
        try:
            all_grades = self.get_all_grades_data()
            
            total_users = len(all_grades)
            total_courses = sum(grades_data.get("total_courses", 0) for grades_data in all_grades)
            
            # Get recent updates (last 24 hours)
            recent_updates = 0
            for grades_data in all_grades:
                last_updated = grades_data.get("last_updated")
                if last_updated:
                    try:
                        last_update_time = datetime.fromisoformat(last_updated)
                        if (datetime.now() - last_update_time).days < 1:
                            recent_updates += 1
                    except:
                        pass
            
            return {
                "total_users": total_users,
                "total_courses": total_courses,
                "recent_updates": recent_updates,
                "last_backup": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting grades summary: {e}")
            return {
                "total_users": 0,
                "total_courses": 0,
                "recent_updates": 0,
                "last_backup": datetime.now().isoformat()
            } 