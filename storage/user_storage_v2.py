#!/usr/bin/env python3
"""
User Storage V2 - Clean PostgreSQL-based user storage
"""

import logging
from datetime import datetime, timezone
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
    
    def save_user(self, telegram_id: int, username: str, token: str, user_data: Dict[str, Any], encrypted_password: str = "", password_stored: bool = False, password_consent_given: bool = False) -> bool:
        """Save or update user data"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                firstname = str(user_data.get("firstname")) if user_data.get("firstname") is not None else ""
                lastname = str(user_data.get("lastname")) if user_data.get("lastname") is not None else ""
                fullname = str(user_data.get("fullname")) if user_data.get("fullname") is not None else ""
                email = str(user_data.get("email")) if user_data.get("email") is not None else ""
                token_expired_notified = bool(user_data.get("token_expired_notified", False))
                if user:
                    user.username = str(username) if username is not None else ""  # type: ignore
                    user.token = str(token) if token is not None else ""  # type: ignore
                    user.firstname = firstname  # type: ignore
                    user.lastname = lastname  # type: ignore
                    user.fullname = fullname  # type: ignore
                    user.email = email  # type: ignore
                    user.last_login = datetime.now(timezone.utc)  # type: ignore
                    user.is_active = True  # type: ignore
                    user.token_expired_notified = token_expired_notified  # type: ignore
                    user.encrypted_password = str(encrypted_password) if encrypted_password is not None else ""  # type: ignore
                    user.password_stored = bool(password_stored)  # type: ignore
                    user.password_consent_given = bool(password_consent_given)  # type: ignore
                    session.commit()
                    logger.info(f"✅ User {username} (ID: {telegram_id}) updated")
                else:
                    new_user = User(
                        telegram_id=telegram_id,
                        username=str(username) if username is not None else "",  # type: ignore
                        token=str(token) if token is not None else "",  # type: ignore
                        firstname=firstname,  # type: ignore
                        lastname=lastname,  # type: ignore
                        fullname=fullname,  # type: ignore
                        email=email,  # type: ignore
                        registration_date=datetime.now(timezone.utc),  # type: ignore
                        last_login=datetime.now(timezone.utc),  # type: ignore
                        is_active=True,  # type: ignore
                        token_expired_notified=token_expired_notified,  # type: ignore
                        encrypted_password=str(encrypted_password) if encrypted_password is not None else "",  # type: ignore
                        password_stored=bool(password_stored),  # type: ignore
                        password_consent_given=bool(password_consent_given),  # type: ignore
                    )
                    session.add(new_user)
                    session.commit()
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
                        "username_unique": getattr(user, 'username_unique', user.username),
                        "token": user.token,
                        "firstname": user.firstname,
                        "lastname": user.lastname,
                        "fullname": user.fullname,
                        "email": user.email,
                        "registration_date": user.registration_date.isoformat() if hasattr(user.registration_date, 'isoformat') else None,  # type: ignore
                        "last_login": user.last_login.isoformat() if hasattr(user.last_login, 'isoformat') else None,  # type: ignore
                        "is_active": bool(user.is_active),
                        "token_expired_notified": bool(user.token_expired_notified),
                        "encrypted_password": user.encrypted_password if user.encrypted_password is not None else "",
                        "password_stored": bool(user.password_stored),
                        "password_consent_given": bool(user.password_consent_given),
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
                        "registration_date": user.registration_date.isoformat() if hasattr(getattr(user, 'registration_date', None), 'isoformat') else None,  # type: ignore
                        "last_login": user.last_login.isoformat() if hasattr(getattr(user, 'last_login', None), 'isoformat') else None,  # type: ignore
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
                    session.commit()
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
                    user.token = ""  # type: ignore
                    user.is_active = False  # type: ignore
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
                    user.token_expired_notified = bool(notified)  # type: ignore
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

def migrate_backfill_username_unique(database_url: str):
    """
    For all users where username_unique is NULL or empty, set username_unique = username.
    """
    from storage.models import DatabaseManager, User
    db_manager = DatabaseManager(database_url)
    with db_manager.get_session() as session:
        users = session.query(User).filter((User.username_unique == None) | (User.username_unique == "")).all()
        count = 0
        for user in users:
            user.username_unique = user.username
            count += 1
        session.commit()
        print(f"[MIGRATION] Backfilled username_unique for {count} users.")

if __name__ == "__main__":
    import os
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Please set the DATABASE_URL environment variable.")
    else:
        migrate_backfill_username_unique(db_url) 