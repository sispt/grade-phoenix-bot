"""
User Storage System v2
Handles user data storage and management using PostgreSQL
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging
import re

from .models import DatabaseManager, User
from .grade_storage_v2 import GradeStorageV2

logger = logging.getLogger(__name__)

class UserStorageV2:
    """User storage system using PostgreSQL"""
    
    def __init__(self, database_url: str, grade_storage: Optional[GradeStorageV2] = None):
        # Use MYSQL_URL if set, otherwise fallback to database_url argument
        import os
        env_url = os.getenv("MYSQL_URL") or database_url
        self.db_manager = DatabaseManager(env_url)
        self._ensure_tables()
        self.grade_storage = grade_storage
    
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
    
    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create a new user"""
        try:
            with self._get_session() as session:
                # Check if user already exists
                existing_user = session.query(User).filter(
                    or_(
                        User.username == user_data.get('username'),
                        User.telegram_id == user_data.get('telegram_id')
                    )
                ).first()
                
                if existing_user:
                    logger.warning(f"User already exists: {user_data.get('username')}")
                    return False
                
                # Create new user
                user = User(
                    username=user_data.get('username'),
                    telegram_id=user_data.get('telegram_id'),
                    fullname=user_data.get('fullname'),
                    firstname=user_data.get('firstname'),
                    lastname=user_data.get('lastname'),
                    email=user_data.get('email'),
                    session_token=user_data.get('session_token'),
                    token_expires_at=user_data.get('token_expires_at'),
                    is_active=True
                )
                
                session.add(user)
                session.commit()
                logger.info(f"✅ User created successfully: {user_data.get('username')}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to create user: {e}")
            return False
    
    def get_user(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Get user by username or telegram_id"""
        try:
            with self._get_session() as session:
                filters = [User.username == identifier]
                if (isinstance(identifier, str) and identifier.isdigit()):
                    filters.append(User.telegram_id == int(identifier))
                elif isinstance(identifier, int):
                    filters.append(User.telegram_id == identifier)
                user = session.query(User).filter(or_(*filters)).first()
                
                if user:
                    return self._user_to_dict(user)
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get user: {e}")
            return None
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by telegram ID"""
        try:
            with self._get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                if user:
                    return self._user_to_dict(user)
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get user by telegram_id: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            with self._get_session() as session:
                user = session.query(User).filter(User.username == username).first()
                if user:
                    return self._user_to_dict(user)
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get user by username: {e}")
            return None
    
    def update_user(self, username: str, update_data: Dict[str, Any]) -> bool:
        """Update user information"""
        try:
            with self._get_session() as session:
                user = session.query(User).filter(User.username == username).first()
                if not user:
                    logger.warning(f"User not found: {username}")
                    return False
                
                # Update fields
                for key, value in update_data.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                setattr(user, 'updated_at', datetime.now(timezone.utc))
                session.commit()
                logger.info(f"✅ User updated successfully: {username}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to update user: {e}")
            return False
    
    def update_session_token(self, username: str, token: str, expires_at: datetime) -> bool:
        """Update user session token"""
        try:
            with self._get_session() as session:
                user = session.query(User).filter(User.username == username).first()
                if not user:
                    return False
                
                setattr(user, 'session_token', token)
                setattr(user, 'token_expires_at', expires_at)
                setattr(user, 'last_login', datetime.now(timezone.utc))
                setattr(user, 'updated_at', datetime.now(timezone.utc))
                
                session.commit()
                logger.info(f"✅ Session token updated for: {username}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to update session token: {e}")
            return False
    
    def delete_user(self, username: str) -> bool:
        """Delete user and all associated grades"""
        try:
            # Cascade delete grades first
            if self.grade_storage:
                self.grade_storage.delete_user_grades(username)
            with self._get_session() as session:
                user = session.query(User).filter(User.username == username).first()
                if not user:
                    logger.warning(f"User not found for deletion: {username}")
                    return False
                session.delete(user)
                session.commit()
                logger.info(f"✅ User deleted successfully: {username}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to delete user: {e}")
            return False
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all active users"""
        try:
            with self._get_session() as session:
                users = session.query(User).filter(User.is_active == True).all()
                return [self._user_to_dict(user) for user in users]
                
        except Exception as e:
            logger.error(f"❌ Failed to get all users: {e}")
            return []
    
    def is_user_registered(self, identifier: str) -> bool:
        """Check if user is registered by username or telegram_id"""
        try:
            with self._get_session() as session:
                filters = [User.username == identifier]
                if (isinstance(identifier, str) and identifier.isdigit()):
                    filters.append(User.telegram_id == int(identifier))
                elif isinstance(identifier, int):
                    filters.append(User.telegram_id == identifier)
                user = session.query(User).filter(or_(*filters)).first()
                return user is not None
                
        except Exception as e:
            logger.error(f"❌ Failed to check user registration: {e}")
            return False
    
    def get_users_with_expired_tokens(self) -> List[Dict[str, Any]]:
        """Get users with expired session tokens"""
        try:
            with self._get_session() as session:
                now = datetime.now(timezone.utc)
                users = session.query(User).filter(
                    and_(
                        User.token_expires_at.isnot(None),
                        User.token_expires_at < now
                    )
                ).all()
                return [self._user_to_dict(user) for user in users]
                
        except Exception as e:
            logger.error(f"❌ Failed to get users with expired tokens: {e}")
            return []
    
    def update_token_expired_notified(self, username: str, notified: bool = True) -> bool:
        """Mark that user has been notified about expired token"""
        try:
            with self._get_session() as session:
                user = session.query(User).filter(User.username == username).first()
                if not user:
                    return False
                # Assign directly to ORM attributes
                user.session_expired_notified = notified
                user.updated_at = datetime.now(timezone.utc)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Failed to update token expired notification: {e}")
            return False
    
    def get_user_count(self) -> int:
        """Get total number of active users"""
        try:
            with self._get_session() as session:
                return session.query(User).filter(User.is_active == True).count()
                
        except Exception as e:
            logger.error(f"❌ Failed to get user count: {e}")
            return 0
    
    def search_users(self, query: str) -> List[Dict[str, Any]]:
        """Search users by username, fullname, or email"""
        try:
            with self._get_session() as session:
                users = session.query(User).filter(
                    and_(
                        User.is_active == True,
                        or_(
                            User.username.ilike(f"%{query}%"),
                            User.fullname.ilike(f"%{query}%"),
                            User.email.ilike(f"%{query}%")
                        )
                    )
                ).all()
                return [self._user_to_dict(user) for user in users]
                
        except Exception as e:
            logger.error(f"❌ Failed to search users: {e}")
            return []
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert User object to dictionary"""
        return {
            'username': user.username,
            'telegram_id': user.telegram_id,
            'fullname': user.fullname,
            'firstname': user.firstname,
            'lastname': user.lastname,
            'email': user.email,
            'session_token': user.session_token,
            'token_expires_at': user.token_expires_at.isoformat() if getattr(user, 'token_expires_at', None) is not None else None,
            'last_login': user.last_login.isoformat() if getattr(user, 'last_login', None) is not None else None,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if getattr(user, 'created_at', None) is not None else None,
            'updated_at': user.updated_at.isoformat() if getattr(user, 'updated_at', None) is not None else None,
            'session_expired_notified': user.session_expired_notified,
            'encrypted_password': user.encrypted_password,
            'password_stored': user.password_stored,
            'password_consent_given': user.password_consent_given,
        } 