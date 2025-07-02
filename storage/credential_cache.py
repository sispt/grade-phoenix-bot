"""
🔐 Credential Test Cache System
"""
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from config import CONFIG
from storage.models import DatabaseManager, CredentialTest

logger = logging.getLogger(__name__)

class CredentialCache:
    """Database-based credential test cache system"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db_manager = database_manager
        self.cache_duration_hours = CONFIG.get("CREDENTIAL_CACHE_DURATION_HOURS", 24)
    
    def _hash_password(self, password: str) -> str:
        """Hash password for secure storage"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _get_cache_key(self, username: str, password: str) -> Tuple[str, str]:
        """Get cache key components"""
        return username, self._hash_password(password)
    
    def is_credential_tested(self, username: str, password: str) -> bool:
        """Check if credentials have been tested recently"""
        try:
            username_key, password_hash = self._get_cache_key(username, password)
            
            with self.db_manager.get_session() as session:
                # Check for recent test within cache duration
                cache_cutoff = datetime.utcnow() - timedelta(hours=self.cache_duration_hours)
                
                existing_test = session.query(CredentialTest).filter(
                    CredentialTest.username == username_key,
                    CredentialTest.password_hash == password_hash,
                    CredentialTest.test_date >= cache_cutoff
                ).first()
                
                return existing_test is not None
                
        except SQLAlchemyError as e:
            logger.error(f"Database error checking credential cache: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking credential cache: {e}")
            return False
    
    def get_cached_result(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Get cached test result for credentials"""
        try:
            username_key, password_hash = self._get_cache_key(username, password)
            
            with self.db_manager.get_session() as session:
                # Get most recent test result
                cache_cutoff = datetime.utcnow() - timedelta(hours=self.cache_duration_hours)
                
                existing_test = session.query(CredentialTest).filter(
                    CredentialTest.username == username_key,
                    CredentialTest.password_hash == password_hash,
                    CredentialTest.test_date >= cache_cutoff
                ).order_by(CredentialTest.test_date.desc()).first()
                
                return existing_test.to_dict() if existing_test else None
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting cached result: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting cached result: {e}")
            return None
    
    def cache_test_result(self, username: str, password: str, test_result: bool, 
                         error_message: Optional[str] = None, response_time_ms: Optional[int] = None,
                         user_agent: Optional[str] = None, ip_address: Optional[str] = None):
        """Cache test result for credentials"""
        try:
            username_key, password_hash = self._get_cache_key(username, password)
            
            with self.db_manager.get_session() as session:
                # Create new test record
                test_record = CredentialTest(
                    username=username_key,
                    password_hash=password_hash,
                    test_result=test_result,
                    test_date=datetime.utcnow(),
                    error_message=error_message,
                    response_time_ms=response_time_ms,
                    user_agent=user_agent,
                    ip_address=ip_address
                )
                
                session.add(test_record)
                session.commit()
                
                logger.info(f"Cached test result for {username}: {'SUCCESS' if test_result else 'FAILED'}")
                
        except SQLAlchemyError as e:
            logger.error(f"Database error caching test result: {e}")
        except Exception as e:
            logger.error(f"Error caching test result: {e}")
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """Get credential test statistics"""
        try:
            with self.db_manager.get_session() as session:
                total_tests = session.query(CredentialTest).count()
                successful_tests = session.query(CredentialTest).filter(CredentialTest.test_result == True).count()
                failed_tests = session.query(CredentialTest).filter(CredentialTest.test_result == False).count()
                
                # Recent tests (last 24 hours)
                recent_cutoff = datetime.utcnow() - timedelta(hours=24)
                recent_tests = session.query(CredentialTest).filter(CredentialTest.test_date >= recent_cutoff).count()
                
                # Average response time
                avg_response_time = session.query(CredentialTest.response_time_ms).filter(
                    CredentialTest.response_time_ms.isnot(None)
                ).all()
                avg_response_time = sum([r[0] for r in avg_response_time]) / len(avg_response_time) if avg_response_time else 0
                
                return {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "failed_tests": failed_tests,
                    "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
                    "recent_tests_24h": recent_tests,
                    "average_response_time_ms": int(avg_response_time)
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting test statistics: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error getting test statistics: {e}")
            return {}
    
    def clear_expired_cache(self, hours: Optional[int] = None) -> int:
        """Clear expired cache entries"""
        try:
            if hours is None:
                hours = self.cache_duration_hours
            
            cutoff_date = datetime.utcnow() - timedelta(hours=hours)
            
            with self.db_manager.get_session() as session:
                deleted_count = session.query(CredentialTest).filter(
                    CredentialTest.test_date < cutoff_date
                ).delete()
                
                session.commit()
                logger.info(f"Cleared {deleted_count} expired cache entries")
                return deleted_count
                
        except SQLAlchemyError as e:
            logger.error(f"Database error clearing expired cache: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
            return 0
    
    def get_recent_tests(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent credential tests"""
        try:
            with self.db_manager.get_session() as session:
                recent_tests = session.query(CredentialTest).order_by(
                    CredentialTest.test_date.desc()
                ).limit(limit).all()
                
                return [test.to_dict() for test in recent_tests]
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting recent tests: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting recent tests: {e}")
            return []
    
    def search_tests_by_username(self, username: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search tests by username"""
        try:
            with self.db_manager.get_session() as session:
                tests = session.query(CredentialTest).filter(
                    CredentialTest.username.ilike(f"%{username}%")
                ).order_by(CredentialTest.test_date.desc()).limit(limit).all()
                
                return [test.to_dict() for test in tests]
                
        except SQLAlchemyError as e:
            logger.error(f"Database error searching tests: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching tests: {e}")
            return []
    
    def get_failed_credentials(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently failed credentials"""
        try:
            with self.db_manager.get_session() as session:
                failed_tests = session.query(CredentialTest).filter(
                    CredentialTest.test_result == False
                ).order_by(CredentialTest.test_date.desc()).limit(limit).all()
                
                return [test.to_dict() for test in failed_tests]
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting failed credentials: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting failed credentials: {e}")
            return []
    
    def get_successful_credentials(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently successful credentials"""
        try:
            with self.db_manager.get_session() as session:
                successful_tests = session.query(CredentialTest).filter(
                    CredentialTest.test_result == True
                ).order_by(CredentialTest.test_date.desc()).limit(limit).all()
                
                return [test.to_dict() for test in successful_tests]
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting successful credentials: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting successful credentials: {e}")
            return [] 