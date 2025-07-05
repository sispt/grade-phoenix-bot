import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from storage.grade_storage_v2 import GradeStorageV2


@pytest.fixture
def grade_storage(tmp_path, monkeypatch):
    monkeypatch.setattr("storage.grade_storage.CONFIG", {"DATA_DIR": str(tmp_path)})
    return GradeStorageV2("sqlite:///test.db")


def test_save_and_get_grades(grade_storage):
    grades = [
        {"code": "MATH101", "name": "Math", "total": 90},
        {"code": "ENG202", "name": "English", "total": 85},
    ]
    grade_storage.save_grades(123, grades)
    result = grade_storage.get_grades(123)
    assert isinstance(result, list)
    assert len(result) == 2
    codes = {g["code"] for g in result}
    assert "MATH101" in codes and "ENG202" in codes


def test_update_grades(grade_storage):
    grades1 = [{"code": "MATH101", "name": "Math", "total": 90}]
    grades2 = [{"code": "MATH101", "name": "Math", "total": 95}]
    grade_storage.save_grades(123, grades1)
    grade_storage.save_grades(123, grades2)
    result = grade_storage.get_grades(123)
    assert result[0]["total"] == 95
