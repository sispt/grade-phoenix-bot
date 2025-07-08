#!/usr/bin/env python3
"""
User Storage V2 - Clean PostgreSQL-based user storage
No password persistence - matches 2.0.1 branch
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.exc import SQLAlchemyError

from storage.models import DatabaseManager, User

logger = logging.getLogger(__name__)


class UserStorageV2:
    """Clean user storage system - no password persistence"""
    
    def __init__(self, database_url: str):
        self.db_manager = DatabaseManager(database_url)
        self.db_manager.create_all_tables()
        logger.info("✅ UserStorageV2 initialized")
    
    def save_user(self, telegram_id: int, username: str, token: str, user_data: Dict[str, Any]) -> bool:
        """Save or update user data"""
        try:
            with self.db_manager.get_session() as session:
                # Check if user exists
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                
                # Extract user info
                firstname = user_data.get("firstname")
                lastname = user_data.get("lastname")
                fullname = user_data.get("fullname")
                email = user_data.get("email")
                token_expired_notified = user_data.get("token_expired_notified", False)
                
                if user:
                    # Update existing user
                    user.username = username
                    user.token = token
                    user.firstname = firstname
                    user.lastname = lastname
                    user.fullname = fullname
                    user.email = email
                    user.last_login = datetime.utcnow()
                    user.is_active = True
                    user.token_expired_notified = token_expired_notified
                    
                    logger.info(f"✅ User {username} (ID: {telegram_id}) updated")
                else:
                    # Create new user
                    new_user = User(
                        telegram_id=telegram_id,
                        username=username,
                        token=token,
                        firstname=firstname,
                        lastname=lastname,
                        fullname=fullname,
                        email=email,
                        registration_date=datetime.utcnow(),
                        last_login=datetime.utcnow(),
                        is_active=True,
                        token_expired_notified=token_expired_notified,
                    )
                    session.add(new_user)
                    logger.info(f"✅ User {username} (ID: {telegram_id}) created")
                
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error saving user {username}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error saving user {username}: {e}")
            return False
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    return {
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "token": user.token,
                        "firstname": user.firstname,
                        "lastname": user.lastname,
                        "fullname": user.fullname,
                        "email": user.email,
                        "registration_date": user.registration_date.isoformat() if user.registration_date else None,
                        "last_login": user.last_login.isoformat() if user.last_login else None,
                        "is_active": user.is_active,
                        "token_expired_notified": user.token_expired_notified,
                    }
                return None
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error getting user {telegram_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error getting user {telegram_id}: {e}")
            return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all active users"""
        try:
            with self.db_manager.get_session() as session:
                users = session.query(User).filter_by(is_active=True).all()
                return [
                    {
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "token": user.token,
                        "firstname": user.firstname,
                        "lastname": user.lastname,
                        "fullname": user.fullname,
                        "email": user.email,
                        "registration_date": user.registration_date.isoformat() if user.registration_date else None,
                        "last_login": user.last_login.isoformat() if user.last_login else None,
                        "is_active": user.is_active,
                        "token_expired_notified": user.token_expired_notified,
                    }
                    for user in users
                ]
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error getting all users: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error getting all users: {e}")
            return []
    
    def is_user_registered(self, telegram_id: int) -> bool:
        """Check if user is registered"""
        return self.get_user(telegram_id) is not None
    
    def delete_user(self, telegram_id: int) -> bool:
        """Delete user by Telegram ID"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    session.delete(user)
                    logger.info(f"✅ User (ID: {telegram_id}) deleted")
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error deleting user {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting user {telegram_id}: {e}")
            return False
    
    def clear_user_token(self, telegram_id: int) -> bool:
        """Clear user's token"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    user.token = None
                    user.is_active = False
                    logger.info(f"✅ Cleared token for user {telegram_id}")
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error clearing token for user {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error clearing token for user {telegram_id}: {e}")
            return False
    
    def update_token_expired_notified(self, telegram_id: int, notified: bool) -> bool:
        """Update token expired notification status"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    user.token_expired_notified = notified
                    logger.info(f"✅ Updated token expired notification for user {telegram_id}: {notified}")
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error updating token expired notification for user {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error updating token expired notification for user {telegram_id}: {e}")
            return False
    
    def _save_users(self):
        """Compatibility method - no-op for PostgreSQL storage"""
        # This method is not needed for PostgreSQL storage as it's handled automatically
        pass 