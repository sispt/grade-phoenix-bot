"""
👥 User Storage System
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..config import CONFIG

logger = logging.getLogger(__name__)

class UserStorage:
    """User data storage system"""
    
    def __init__(self):
        self.data_dir = CONFIG["DATA_DIR"]
        self.users_file = os.path.join(self.data_dir, "users.json")
        self._ensure_data_dir()
        self._load_users()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _load_users(self):
        """Load users from file"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            else:
                self.users = []
                self._save_users()
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            self.users = []
    
    def _save_users(self):
        """Save users to file"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def save_user(self, telegram_id: int, username: str, password: str, token: str, user_data: Dict[str, Any]):
        """Save or update user data"""
        try:
            # Check if user exists
            existing_user = self.get_user(telegram_id)
            
            user_record = {
                "telegram_id": telegram_id,
                "username": username,
                "password": password,
                "token": token,
                "firstname": user_data.get("firstname"),
                "lastname": user_data.get("lastname"),
                "fullname": user_data.get("fullname"),
                "email": user_data.get("email"),
                "registration_date": datetime.now().isoformat(),
                "last_login": datetime.now().isoformat(),
                "is_active": True
            }
            
            if existing_user:
                # Update existing user
                user_record["registration_date"] = existing_user.get("registration_date")
                for i, user in enumerate(self.users):
                    if user.get("telegram_id") == telegram_id:
                        self.users[i] = user_record
                        break
            else:
                # Add new user
                self.users.append(user_record)
            
            self._save_users()
            logger.info(f"User saved: {username} (ID: {telegram_id})")
            
        except Exception as e:
            logger.error(f"Error saving user: {e}")
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by telegram ID"""
        for user in self.users:
            if user.get("telegram_id") == telegram_id:
                return user
        return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        return self.users
    
    def update_user(self, telegram_id: int, user_data: Dict[str, Any]):
        """Update user data"""
        for i, user in enumerate(self.users):
            if user.get("telegram_id") == telegram_id:
                user_data["last_login"] = datetime.now().isoformat()
                self.users[i].update(user_data)
                self._save_users()
                break
    
    def delete_user(self, telegram_id: int) -> bool:
        """Delete user"""
        for i, user in enumerate(self.users):
            if user.get("telegram_id") == telegram_id:
                del self.users[i]
                self._save_users()
                logger.info(f"User deleted: {telegram_id}")
                return True
        return False
    
    def get_active_users(self) -> List[Dict[str, Any]]:
        """Get active users"""
        return [user for user in self.users if user.get("is_active", True)]
    
    def get_users_count(self) -> int:
        """Get total users count"""
        return len(self.users)
    
    def get_active_users_count(self) -> int:
        """Get active users count"""
        return len(self.get_active_users())
    
    def search_user(self, query: str) -> List[Dict[str, Any]]:
        """Search users by username or fullname"""
        results = []
        query_lower = query.lower()
        
        for user in self.users:
            username = user.get("username", "").lower()
            fullname = user.get("fullname", "").lower()
            
            if query_lower in username or query_lower in fullname:
                results.append(user)
        
        return results
    
    def backup_users(self) -> str:
        """Create backup of users data"""
        try:
            backup_file = os.path.join(
                CONFIG.get("BACKUP_DIR", "backups"),
                f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            os.makedirs(os.path.dirname(backup_file), exist_ok=True)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Users backup created: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Error creating users backup: {e}")
            return "" 