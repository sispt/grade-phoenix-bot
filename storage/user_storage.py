"""
Merged User Storage System
Combines file-based and PostgreSQL user storage
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.exc import SQLAlchemyError

from config import CONFIG
from storage.models import User, DatabaseManager

logger = logging.getLogger(__name__)


class UserStorage:
    """File-based user data storage system"""

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
                with open(self.users_file, "r", encoding="utf-8") as f:
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
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving users: {e}")

    def save_user(
        self,
        telegram_id: int,
        username: str,
        password: str,
        token: str,
        user_data: Dict[str, Any],
    ):
        """Save or update user data"""
        try:
            # Check if user already exists
            existing_user = None
            for user in self.users:
                if user.get("telegram_id") == telegram_id:
                    existing_user = user
                    break

            user_info = {
                "telegram_id": telegram_id,
                "username": username,
                "password": None,  # Password is not stored
                "token": token,
                "firstname": user_data.get("firstname"),
                "lastname": user_data.get("lastname"),
                "fullname": user_data.get("fullname"),
                "email": user_data.get("email"),
                "registration_date": datetime.now().isoformat(),
                "last_login": datetime.now().isoformat(),
                "is_active": True,
            }

            if existing_user:
                # Update existing user
                existing_user.update(user_info)
                logger.info(
                    f"✅ User {username} (ID: {telegram_id}) updated in file storage."
                )
            else:
                # Add new user
                self.users.append(user_info)
                logger.info(
                    f"✅ User {username} (ID: {telegram_id}) saved to file storage."
                )

            self._save_users()
            return True
        except Exception as e:
            logger.error(f"❌ Error saving user {username}: {e}")
            return False

    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID"""
        for user in self.users:
            if user.get("telegram_id") == telegram_id:
                return user
        return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        return self.users

    def is_user_registered(self, telegram_id: int) -> bool:
        """Check if user is registered"""
        return self.get_user(telegram_id) is not None

    def delete_user(self, telegram_id: int) -> bool:
        """Delete user by Telegram ID"""
        try:
            self.users = [
                user for user in self.users if user.get("telegram_id") != telegram_id
            ]
            self._save_users()
            logger.info(f"✅ User (ID: {telegram_id}) deleted from file storage.")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting user {telegram_id}: {e}")
            return False

    def update_user(self, telegram_id: int, updates: dict) -> bool:
        """Update fields for a user with the given telegram_id."""
        try:
            for user in self.users:
                if user.get("telegram_id") == telegram_id:
                    user.update(updates)
                    self._save_users()
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Error updating user {telegram_id}: {e}")
            return False


class PostgreSQLUserStorage:
    """PostgreSQL user storage system"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def save_user(
        self,
        telegram_id: int,
        username: str,
        password: str,
        token: str,
        user_data: Dict[str, Any],
    ):
        try:
            with self.db_manager.get_session() as session:
                # Check if user already exists
                user = session.query(User).filter_by(telegram_id=telegram_id).first()

                # Extract user info from user_data passed from API
                firstname = user_data.get("firstname")
                lastname = user_data.get("lastname")
                fullname = user_data.get("fullname")
                email = user_data.get("email")

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
                    logger.info(
                        f"✅ User {username} (ID: {telegram_id}) updated in PostgreSQL."
                    )
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
                    )
                    session.add(new_user)
                    logger.info(
                        f"✅ User {username} (ID: {telegram_id}) saved to PostgreSQL."
                    )

                session.commit()
                return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error saving user {username}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error saving user {username}: {e}")
            return False

    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    return {
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "password": None,  # Password is not stored
                        "token": user.token,
                        "firstname": user.firstname,
                        "lastname": user.lastname,
                        "fullname": user.fullname,
                        "email": user.email,
                        "registration_date": (
                            user.registration_date.isoformat()
                            if user.registration_date
                            else None
                        ),
                        "last_login": (
                            user.last_login.isoformat() if user.last_login else None
                        ),
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
        try:
            with self.db_manager.get_session() as session:
                users = session.query(User).filter_by(is_active=True).all()
                return [
                    {
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "password": None,  # Password is not stored
                        "token": user.token,
                        "firstname": user.firstname,
                        "lastname": user.lastname,
                        "fullname": user.fullname,
                        "email": user.email,
                        "registration_date": (
                            user.registration_date.isoformat()
                            if user.registration_date
                            else None
                        ),
                        "last_login": (
                            user.last_login.isoformat() if user.last_login else None
                        ),
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
        return self.get_user(telegram_id) is not None

    def delete_user(self, telegram_id: int) -> bool:
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    # Delete associated grades first (cascade)
                    from storage.grade_storage import PostgreSQLGradeStorage

                    grade_storage = PostgreSQLGradeStorage(self.db_manager)
                    grade_storage.delete_grades(telegram_id)

                    # Delete user
                    session.delete(user)
                    session.commit()
                    logger.info(
                        f"✅ User (ID: {telegram_id}) deleted from PostgreSQL with cascade."
                    )
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error deleting user {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting user {telegram_id}: {e}")
            return False

    def update_token_expired_notified(self, telegram_id: int, notified: bool) -> bool:
        """Update the token_expired_notified flag for a user."""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    user.token_expired_notified = notified
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error updating token_expired_notified for user {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error updating token_expired_notified for user {telegram_id}: {e}")
            return False

    def clear_user_token(self, telegram_id: int) -> bool:
        """Clear the user's token to force a fresh login."""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    user.token = None
                    user.token_expired_notified = False
                    session.commit()
                    logger.info(f"✅ Cleared token for user {telegram_id}")
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error clearing token for user {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error clearing token for user {telegram_id}: {e}")
            return False
