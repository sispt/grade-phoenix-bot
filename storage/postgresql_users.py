"""
👥 PostgreSQL User Storage System
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from config import CONFIG
from storage.models import DatabaseManager, User

logger = logging.getLogger(__name__)

class PostgreSQLUserStorage:
    """PostgreSQL-based user data storage system"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db_manager = database_manager
    
    def save_user(self, telegram_id: int, username: str, password: str, token: str, user_data: Dict[str, Any]):
        """Save or update user data"""
        try:
            with self.db_manager.get_session() as session:
                # Check if user exists
                existing_user = session.query(User).filter(User.telegram_id == telegram_id).first()
                
                if existing_user:
                    # Update existing user
                    existing_user.username = username
                    existing_user.password = password
                    existing_user.token = token
                    existing_user.firstname = user_data.get("firstname")
                    existing_user.lastname = user_data.get("lastname")
                    existing_user.fullname = user_data.get("fullname")
                    existing_user.email = user_data.get("email")
                    existing_user.last_login = datetime.utcnow()
                    existing_user.is_active = True
                    
                    session.commit()
                    logger.info(f"User updated: {username} (ID: {telegram_id})")
                else:
                    # Create new user
                    new_user = User(
                        telegram_id=telegram_id,
                        username=username,
                        password=password,
                        token=token,
                        firstname=user_data.get("firstname"),
                        lastname=user_data.get("lastname"),
                        fullname=user_data.get("fullname"),
                        email=user_data.get("email"),
                        registration_date=datetime.utcnow(),
                        last_login=datetime.utcnow(),
                        is_active=True
                    )
                    
                    session.add(new_user)
                    session.commit()
                    logger.info(f"User created: {username} (ID: {telegram_id})")
                
        except SQLAlchemyError as e:
            logger.error(f"Database error saving user: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            raise
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by telegram ID"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                return user.to_dict() if user else None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        try:
            with self.db_manager.get_session() as session:
                users = session.query(User).all()
                return [user.to_dict() for user in users]
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all users: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def update_user(self, telegram_id: int, user_data: Dict[str, Any]):
        """Update user data"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                if user:
                    for key, value in user_data.items():
                        if hasattr(user, key):
                            setattr(user, key, value)
                    user.last_login = datetime.utcnow()
                    session.commit()
                    logger.info(f"User updated: {telegram_id}")
        except SQLAlchemyError as e:
            logger.error(f"Database error updating user: {e}")
        except Exception as e:
            logger.error(f"Error updating user: {e}")
    
    def delete_user(self, telegram_id: int) -> bool:
        """Delete user"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                if user:
                    session.delete(user)
                    session.commit()
                    logger.info(f"User deleted: {telegram_id}")
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting user: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    def get_active_users(self) -> List[Dict[str, Any]]:
        """Get active users"""
        try:
            with self.db_manager.get_session() as session:
                users = session.query(User).filter(User.is_active == True).all()
                return [user.to_dict() for user in users]
        except SQLAlchemyError as e:
            logger.error(f"Database error getting active users: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    def get_users_count(self) -> int:
        """Get total users count"""
        try:
            with self.db_manager.get_session() as session:
                return session.query(User).count()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting users count: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error getting users count: {e}")
            return 0
    
    def get_active_users_count(self) -> int:
        """Get active users count"""
        try:
            with self.db_manager.get_session() as session:
                return session.query(User).filter(User.is_active == True).count()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting active users count: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error getting active users count: {e}")
            return 0
    
    def search_user(self, query: str) -> List[Dict[str, Any]]:
        """Search users by username or fullname"""
        try:
            with self.db_manager.get_session() as session:
                users = session.query(User).filter(
                    (User.username.ilike(f"%{query}%")) |
                    (User.fullname.ilike(f"%{query}%"))
                ).all()
                return [user.to_dict() for user in users]
        except SQLAlchemyError as e:
            logger.error(f"Database error searching users: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
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
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                if user:
                    user.token = token
                    user.last_login = datetime.utcnow()
                    session.commit()
                    logger.info(f"Token updated for user {telegram_id}")
        except SQLAlchemyError as e:
            logger.error(f"Database error updating token: {e}")
        except Exception as e:
            logger.error(f"Error updating token: {e}")
    
    def invalidate_user_session(self, telegram_id: int):
        """Invalidate user session (clear token)"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                if user:
                    user.token = None
                    user.is_active = False
                    session.commit()
                    logger.info(f"Session invalidated for user {telegram_id}")
        except SQLAlchemyError as e:
            logger.error(f"Database error invalidating session: {e}")
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            with self.db_manager.get_session() as session:
                total_users = session.query(User).count()
                active_users = session.query(User).filter(User.is_active == True).count()
                users_with_tokens = session.query(User).filter(User.token.isnot(None)).count()
                
                return {
                    "total_users": total_users,
                    "active_users": active_users,
                    "users_with_tokens": users_with_tokens,
                    "inactive_users": total_users - active_users
                }
        except SQLAlchemyError as e:
            logger.error(f"Database error getting session stats: {e}")
            return {"total_users": 0, "active_users": 0, "users_with_tokens": 0, "inactive_users": 0}
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {"total_users": 0, "active_users": 0, "users_with_tokens": 0, "inactive_users": 0} 