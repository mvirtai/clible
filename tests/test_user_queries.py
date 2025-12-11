import pytest
from app.db.queries import QueryDB

@pytest.fixture
def db():
    return QueryDB()

def test_create_user(db):
    user_id = db.create_user("test_user")
    assert user_id is not None
    assert db.get_user_by_id(user_id) is not None

def test_get_user_by_name(db):
    user_id = db.create_user("test_user")
    assert user_id is not None
    assert db.get_user_by_name("test_user") is not None

def test_list_users(db):
    users = db.list_users()
    assert len(users) > 0

def test_get_or_create_default_user(db):
    default_user_id = db.get_or_create_default_user()
    assert default_user_id is not None
    assert db.get_user_by_id(default_user_id) is not None