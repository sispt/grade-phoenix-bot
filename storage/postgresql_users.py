"""
PostgreSQL User Storage System
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from storage.models import Base, User, DatabaseManager # Import User model
from config import CONFIG # Assuming CONFIG holds encryption settings if used
from utils.security_enhancements import hash_password, verify_password, migrate_plain_password

logger = logging.getLogger(__name__)

class PostgreSQLUserStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        # In a real app, migrations handle table creation.
        # For simple setup, can call create_all here if migrations.py isn't used automatically.
        # Base.metadata.create_all(bind=self.db_manager.engine)

    def save_user(self, telegram_id: int, username: str, password: str, token: str, user_data: Dict[str, Any]):
        try:
            with self.db_manager.get_session() as session:
                # Check if user already exists
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                
                # Extract user info from user_data passed from API
                firstname = user_data.get("firstname")
                lastname = user_data.get("lastname")
                fullname = user_data.get("fullname")
                email = user_data.get("email")

                # Hash password for secure storage
                hashed_password = hash_password(password)

                if user:
                    # Update existing user
                    user.username = username
                    user.password = hashed_password  # Store hashed password
                    user.token = token
                    user.firstname = firstname
                    user.lastname = lastname
                    user.fullname = fullname
                    user.email = email
                    user.last_login = datetime.utcnow()
                    user.is_active = True
                    logger.info(f"✅ User {username} (ID: {telegram_id}) updated in PostgreSQL with hashed password.")
                else:
                    # Create new user
                    user = User(
                        telegram_id=telegram_id,
                        username=username,
                        password=hashed_password,  # Store hashed password
                        token=token,
                        firstname=firstname,
                        lastname=lastname,
                        fullname=fullname,
                        email=email,
                        registration_date=datetime.utcnow(),
                        last_login=datetime.utcnow(),
                        is_active=True
                    )
                    session.add(user)
                    logger.info(f"✅ New user {username} (ID: {telegram_id}) added to PostgreSQL with hashed password.")
                session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Error saving user {username} (ID: {telegram_id}) to PostgreSQL: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Unexpected error in save_user for {telegram_id}: {e}", exc_info=True)

    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    return {
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "password": user.password,
                        "token": user.token,
                        "firstname": user.firstname,
                        "lastname": user.lastname,
                        "fullname": user.fullname,
                        "email": user.email,
                        "registration_date": user.registration_date.isoformat() if user.registration_date else None,
                        "last_login": user.last_login.isoformat() if user.last_login else None,
                        "is_active": user.is_active
                    }
                return None
        except SQLAlchemyError as e:
            logger.error(f"❌ Error retrieving user {telegram_id} from PostgreSQL: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error in get_user for {telegram_id}: {e}", exc_info=True)
            return None

    def is_user_registered(self, telegram_id: int) -> bool:
        try:
            with self.db_manager.get_session() as session:
                return session.query(User).filter_by(telegram_id=telegram_id).count() > 0
        except SQLAlchemyError as e:
            logger.error(f"❌ Error checking user registration for {telegram_id}: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error in is_user_registered for {telegram_id}: {e}", exc_info=True)
            return False

    def update_user_token(self, telegram_id: int, new_token: str):
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    user.token = new_token
                    user.last_login = datetime.utcnow() # Update last login on token refresh
                    session.commit()
                    logger.info(f"✅ Token updated for user {telegram_id} in PostgreSQL.")
                else:
                    logger.warning(f"⚠️ User {telegram_id} not found for token update in PostgreSQL.")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Error updating token for user {telegram_id} in PostgreSQL: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Unexpected error in update_user_token for {telegram_id}: {e}", exc_info=True)

    def get_user_session(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        # This function fetches enough data to resume a session
        user = self.get_user(telegram_id)
        if user:
            return {
                "telegram_id": user["telegram_id"],
                "username": user["username"],
                "password": user["password"],
                "token": user["token"]
            }
        return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        try:
            with self.db_manager.get_session() as session:
                users = session.query(User).all()
                return [{
                    "telegram_id": u.telegram_id,
                    "username": u.username,
                    "password": u.password, # Be cautious with exposing raw passwords
                    "token": u.token,
                    "firstname": u.firstname,
                    "lastname": u.lastname,
                    "fullname": u.fullname,
                    "email": u.email,
                    "registration_date": u.registration_date.isoformat() if u.registration_date else None,
                    "last_login": u.last_login.isoformat() if u.last_login else None,
                    "is_active": u.is_active
                } for u in users]
        except SQLAlchemyError as e:
            logger.error(f"❌ Error getting all users from PostgreSQL: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error in get_all_users: {e}", exc_info=True)
            return []

    def get_users_count(self) -> int:
        try:
            with self.db_manager.get_session() as session:
                return session.query(User).count()
        except SQLAlchemyError as e:
            logger.error(f"❌ Error getting users count from PostgreSQL: {e}", exc_info=True)
            return 0
        except Exception as e:
            logger.error(f"❌ Unexpected error in get_users_count: {e}", exc_info=True)
            return 0

    def get_active_users_count(self) -> int:
        try:
            with self.db_manager.get_session() as session:
                return session.query(User).filter_by(is_active=True).count()
        except SQLAlchemyError as e:
            logger.error(f"❌ Error getting active users count from PostgreSQL: {e}", exc_info=True)
            return 0
        except Exception as e:
            logger.error(f"❌ Unexpected error in get_active_users_count: {e}", exc_info=True)
            return 0

    def get_active_users(self) -> List[Dict[str, Any]]:
        # This method is used by the notification loop
        try:
            with self.db_manager.get_session() as session:
                users = session.query(User).filter_by(is_active=True).all()
                return [{
                    "telegram_id": u.telegram_id,
                    "username": u.username,
                    "password": u.password, # For re-login attempt, handle securely
                    "token": u.token
                } for u in users]
        except SQLAlchemyError as e:
            logger.error(f"❌ Error getting active users for notification check: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error in get_active_users: {e}", exc_info=True)
            return []

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
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user and user.password:
                    return verify_password(plain_password, user.password)
                return False
        except SQLAlchemyError as e:
            logger.error(f"❌ Error verifying password for user {telegram_id}: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error in verify_user_password for {telegram_id}: {e}", exc_info=True)
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
            with self.db_manager.get_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    # Hash the plain password
                    hashed_password = hash_password(plain_password)
                    user.password = hashed_password
                    session.commit()
                    logger.info(f"✅ Password migrated for user {telegram_id}")
                    return True
                return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Error migrating password for user {telegram_id}: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error in migrate_user_password for {telegram_id}: {e}", exc_info=True)
            return False