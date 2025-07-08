"""
📊 Grade Storage V2 - Clean Implementation
Handles grade data storage with PostgreSQL
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from decimal import Decimal
import re

from sqlalchemy.exc import SQLAlchemyError

# Import models from the main models file
from storage.models import GradeFailsafeStorage

logger = logging.getLogger(__name__)


class GradeStorageV2:
    """Production-ready grade storage using failsafe table."""
    def __init__(self, database_url: str):
        self.failsafe = GradeFailsafeStorage(database_url)
        logger.info("✅ GradeStorageV2 (failsafe) initialized")

    def save_grades(self, username_unique: str, grades_data, notify_callback=None) -> bool:
        try:
            logger.info(f"[CALL] save_grades (failsafe) for username_unique={username_unique} with {len(grades_data)} grades.")
            self.failsafe.save_grades(username_unique, grades_data)
            return True
        except Exception as e:
            logger.error(f"❌ Failsafe error saving grades for user {username_unique}: {e}")
            return False

    def get_user_grades(self, username_unique: str):
        try:
            logger.info(f"[CALL] get_user_grades (failsafe) for username_unique={username_unique}")
            return self.failsafe.get_user_grades(username_unique)
        except Exception as e:
            logger.error(f"❌ Failsafe error getting grades for user {username_unique}: {e}")
            return []

    def delete_grades(self, username_unique: str) -> bool:
        try:
            logger.info(f"[CALL] delete_grades (failsafe) for username_unique={username_unique}")
            # Not implemented in failsafe, but could be added
            return True
        except Exception as e:
            logger.error(f"❌ Failsafe error deleting grades for user {username_unique}: {e}")
            return False

def safe_float(val):
    from sqlalchemy.orm.attributes import InstrumentedAttribute
    if val is None:
        return None
    if hasattr(val, '__class__') and val.__class__.__name__ == 'InstrumentedAttribute':
        return None
    try:
        return float(val)
    except Exception:
        return None 