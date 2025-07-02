import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from storage.user_storage import UserStorage

@pytest.fixture
def user_storage(tmp_path, monkeypatch):
    # Use a temp directory for test isolation
    monkeypatch.setattr('storage.user_storage.CONFIG', {"DATA_DIR": str(tmp_path)})
    return UserStorage()

def test_save_and_get_user(user_storage):
    user_storage.save_user(123, 'testuser', 'pass', 'token', {'fullname': 'Test User'})
    user = user_storage.get_user(123)
    assert user is not None
    assert user['username'] == 'testuser'
    assert user['fullname'] == 'Test User'

def test_update_user(user_storage):
    user_storage.save_user(123, 'testuser', 'pass', 'token', {'fullname': 'Test User'})
    user_storage.update_user(123, {'fullname': 'Updated User'})
    user = user_storage.get_user(123)
    assert user['fullname'] == 'Updated User'

def test_delete_user(user_storage):
    user_storage.save_user(123, 'testuser', 'pass', 'token', {'fullname': 'Test User'})
    assert user_storage.delete_user(123)
    assert user_storage.get_user(123) is None

def test_get_all_users(user_storage):
    user_storage.save_user(1, 'a', 'p', 't', {'fullname': 'A'})
    user_storage.save_user(2, 'b', 'p', 't', {'fullname': 'B'})
    users = user_storage.get_all_users()
    assert len(users) == 2
    usernames = {u['username'] for u in users}
    assert 'a' in usernames and 'b' in usernames 