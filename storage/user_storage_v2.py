"""
👤 User Storage V2 - Clean Implementation
Handles user data storage with PostgreSQL
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

Base = declarative_base()


class User(Base):
    """User model for database storage"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False, index=True)
    token = Column(String(500), nullable=True)
    firstname = Column(String(100), nullable=True)
    lastname = Column(String(100), nullable=True)
    fullname = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
    registration_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_telegram_id', 'telegram_id'),
        Index('idx_user_username', 'username'),
        Index('idx_user_active', 'is_active'),
    )


class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            raise


class UserStorageV2:
    """Clean user storage system"""
    
    def __init__(self, database_url: str):
        self.db_manager = DatabaseManager(database_url)
        self.db_manager.create_tables()
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