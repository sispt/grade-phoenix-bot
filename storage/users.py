"""
Handles user data storage and retrieval.
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from config import CONFIG
from utils.security_enhancements import hash_password, verify_password, migrate_plain_password

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
            
            # Hash password for secure storage
            hashed_password = hash_password(password)
            
            user_record = {
                "telegram_id": telegram_id,
                "username": username,
                "password": hashed_password,  # Store hashed password
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
            logger.info(f"User saved with hashed password: {username} (ID: {telegram_id})")
            
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
    
    def is_user_registered(self, telegram_id: int) -> bool:
        """Check if user is registered"""
        return self.get_user(telegram_id) is not None
    
    def get_user_session(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user session data (username, password, token)"""
        user = self.get_user(telegram_id)
        if user and user.get("is_active", True):
            return {
                "username": user.get("username"),
                "password": user.get("password"),
                "token": user.get("token"),
                "last_login": user.get("last_login")
            }
        return None
    
    def update_user_token(self, telegram_id: int, token: str):
        """Update user's authentication token"""
        for i, user in enumerate(self.users):
            if user.get("telegram_id") == telegram_id:
                self.users[i]["token"] = token
                self.users[i]["last_login"] = datetime.now().isoformat()
                self._save_users()
                logger.info(f"Token updated for user {telegram_id}")
                break
    
    def invalidate_user_session(self, telegram_id: int):
        """Invalidate user session (clear token)"""
        for i, user in enumerate(self.users):
            if user.get("telegram_id") == telegram_id:
                self.users[i]["token"] = None
                self.users[i]["is_active"] = False
                self._save_users()
                logger.info(f"Session invalidated for user {telegram_id}")
                break
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        total_users = len(self.users)
        active_users = len([u for u in self.users if u.get("is_active", True)])
        users_with_tokens = len([u for u in self.users if u.get("token")])
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "users_with_tokens": users_with_tokens,
            "inactive_users": total_users - active_users
        }

    def verify_user_password(self, telegram_id: int, plain_password: str) -> bool:
        """
        Verify a user's password against the stored hash
        
        Args:
            telegram_id: User's Telegram ID
            plain_password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            user = self.get_user(telegram_id)
            if user and user.get("password"):
                return verify_password(plain_password, user["password"])
            return False
        except Exception as e:
            logger.error(f"Error verifying password for user {telegram_id}: {e}")
            return False

    def migrate_user_password(self, telegram_id: int, plain_password: str) -> bool:
        """
        Migrate a user's plain password to hashed format
        
        Args:
            telegram_id: User's Telegram ID
            plain_password: Plain text password to hash and store
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            for i, user in enumerate(self.users):
                if user.get("telegram_id") == telegram_id:
                    # Hash the plain password
                    hashed_password = hash_password(plain_password)
                    self.users[i]["password"] = hashed_password
                    self._save_users()
                    logger.info(f"Password migrated for user {telegram_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error migrating password for user {telegram_id}: {e}")
            return False 