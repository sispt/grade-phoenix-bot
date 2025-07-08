import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from storage.grade_storage_v2 import GradeStorageV2
from storage.user_storage_v2 import UserStorageV2
from config import CONFIG
from storage.models import Base, DatabaseManager


@pytest.fixture
def grade_storage(tmp_path, monkeypatch):
    # Use V2 storage with test database
    return GradeStorageV2("sqlite:///test.db")


# Use a string username for grade storage tests
USERNAME = "testuser"

def test_save_and_get_grades():
    # Use a shared DatabaseManager for both storages
    db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
    db_manager.drop_all_tables()
    db_manager.create_all_tables()
    from storage.user_storage_v2 import UserStorageV2
    from storage.grade_storage_v2 import GradeStorageV2
    user_storage = UserStorageV2.__new__(UserStorageV2)
    user_storage.db_manager = db_manager
    grade_storage = GradeStorageV2.__new__(GradeStorageV2)
    grade_storage.db_manager = db_manager
    user_storage.save_user(telegram_id=999, username=USERNAME, token="", user_data={})
    grades = [
        {"code": "MATH101", "name": "Math", "total": 90},
        {"code": "ENG202", "name": "English", "total": 85},
    ]
    grade_storage.save_grades(USERNAME, grades)
    result = grade_storage.get_user_grades(USERNAME)
    assert any(g["code"] == "MATH101" and str(g["total"]) == "90" for g in result)
    assert any(g["code"] == "ENG202" and str(g["total"]) == "85" for g in result)


def test_update_grades():
    # Use a shared DatabaseManager for both storages
    db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
    db_manager.drop_all_tables()
    db_manager.create_all_tables()
    from storage.user_storage_v2 import UserStorageV2
    from storage.grade_storage_v2 import GradeStorageV2
    user_storage = UserStorageV2.__new__(UserStorageV2)
    user_storage.db_manager = db_manager
    grade_storage = GradeStorageV2.__new__(GradeStorageV2)
    grade_storage.db_manager = db_manager
    username = "testuser2"
    user_storage.save_user(telegram_id=1000, username=username, token="", user_data={})
    grades1 = [{"code": "MATH101", "name": "Math", "total": 90}]
    grades2 = [{"code": "MATH101", "name": "Math", "total": 95}]
    grade_storage.save_grades(username, grades1)
    grade_storage.save_grades(username, grades2)
    result = grade_storage.get_user_grades(username)
    assert any(g["code"] == "MATH101" and str(g["total"]) == "95" for g in result)
