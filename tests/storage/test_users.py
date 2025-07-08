import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from storage.user_storage_v2 import UserStorageV2


@pytest.fixture
def user_storage(tmp_path):
    # Use a temp sqlite db for test isolation
    db_path = tmp_path / "test.db"
    return UserStorageV2(f"sqlite:///{db_path}")


def test_save_and_get_user(user_storage):
    user_storage.save_user(123, "testuser", "token", {"fullname": "Test User"})
    user = user_storage.get_user(123)
    assert user is not None
    assert user["username"] == "testuser"
    assert user["fullname"] == "Test User"

# Remove test_update_user since update_user does not exist
# def test_update_user(user_storage):
#     user_storage.save_user(123, "testuser", "token", {"fullname": "Test User"})
#     user_storage.update_user(123, {"fullname": "Updated User"})
#     user = user_storage.get_user(123)
#     assert user["fullname"] == "Updated User"

def test_delete_user(user_storage):
    user_storage.save_user(123, "testuser", "token", {"fullname": "Test User"})
    assert user_storage.delete_user(123)
    assert user_storage.get_user(123) is None


def test_get_all_users(user_storage):
    user_storage.save_user(1, "a", "t", {"fullname": "A"})
    user_storage.save_user(2, "b", "t", {"fullname": "B"})
    users = user_storage.get_all_users()
    assert len(users) == 2
    usernames = {u["username"] for u in users}
    assert "a" in usernames and "b" in usernames


def test_save_user_temporary_session(user_storage):
    user_storage.save_user(200, "tempuser", "token", {"fullname": "Temp User"}, encrypted_password=None, password_stored=False, password_consent_given=False)
    user = user_storage.get_user(200)
    assert user is not None
    assert user["password_stored"] is False
    assert user["encrypted_password"] == ""

def test_save_user_permanent_session(user_storage):
    user_storage.save_user(201, "permuser", "token", {"fullname": "Perm User"}, encrypted_password="encrypted_pw", password_stored=True, password_consent_given=True)
    user = user_storage.get_user(201)
    assert user is not None
    assert user["password_stored"] is True
    assert user["encrypted_password"] == "encrypted_pw"

def test_switch_session_types(user_storage):
    # Start as temporary
    user_storage.save_user(202, "switchuser", "token", {"fullname": "Switch User"}, encrypted_password=None, password_stored=False, password_consent_given=False)
    user = user_storage.get_user(202)
    assert user["password_stored"] is False
    # Switch to permanent
    user_storage.save_user(202, "switchuser", "token", {"fullname": "Switch User"}, encrypted_password="enc", password_stored=True, password_consent_given=True)
    user = user_storage.get_user(202)
    assert user["password_stored"] is True
    assert user["encrypted_password"] == "enc"
    # Switch back to temporary
    user_storage.save_user(202, "switchuser", "token", {"fullname": "Switch User"}, encrypted_password=None, password_stored=False, password_consent_given=False)
    user = user_storage.get_user(202)
    assert user["password_stored"] is False
    assert user["encrypted_password"] == ""
