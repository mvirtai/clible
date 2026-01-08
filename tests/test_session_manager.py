"""
Tests for SessionManager class.

Tests cover:
- Session lifecycle (start, end, resume)
- Session persistence (save, delete)
- Security (user ownership verification)
- Error handling (authentication, missing sessions)
"""

import pytest
from pathlib import Path
import tempfile
import sqlite3

from app.session_manager import SessionManager, AuthenticationError
from app.state import AppState
from app.db.queries import QueryDB


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_clible.db"
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def manager_with_user(temp_db):
    """
    Create a SessionManager with a logged-in user.
    
    Returns tuple: (manager, user_id, db_path)
    """
    # Create user in database
    with QueryDB(temp_db) as db:
        user_id = db.create_user("test_user")
    
    # Create manager with test database and simulate login
    manager = SessionManager(db_path=temp_db)
    manager.state.current_user_id = user_id
    
    yield manager, user_id, temp_db
    
    # Cleanup: clear AppState singleton
    manager.state.clear()


@pytest.fixture
def manager_without_user():
    """Create a SessionManager without authentication."""
    manager = SessionManager()
    manager.state.clear()  # Ensure no user is logged in
    yield manager
    manager.state.clear()


class TestSessionLifecycle:
    """Test basic session lifecycle: start, get, end."""
    
    def test_start_session_success(self, manager_with_user):
        """Test starting a new session."""
        manager, user_id, db_path = manager_with_user
        
        session_id = manager.start_session(
            name="Test Session",
            scope="John 1-3",
            temporary=True
        )
        
        assert session_id is not None
        assert manager.state.current_session_id == session_id
        
        # Verify in database
        with QueryDB(db_path) as db:
            session = db.get_session(session_id)
            assert session["name"] == "Test Session"
            assert session["scope"] == "John 1-3"
            assert session["user_id"] == user_id
    
    def test_start_session_without_auth(self, manager_without_user):
        """Test that starting session without auth raises error."""
        manager = manager_without_user
        
        with pytest.raises(AuthenticationError):
            manager.start_session("Test", "scope")
    
    def test_get_current_session(self, manager_with_user):
        """Test retrieving current session details."""
        manager, user_id, db_path = manager_with_user
        
        # Start a session
        session_id = manager.start_session("My Session", "Genesis 1")
        
        # Get current session
        session = manager.get_current_session()
        
        assert session is not None
        assert session["id"] == session_id
        assert session["name"] == "My Session"
    
    def test_get_current_session_when_none_active(self, manager_with_user):
        """Test getting session when none is active."""
        manager, _, _ = manager_with_user
        
        session = manager.get_current_session()
        assert session is None
    
    def test_end_session_success(self, manager_with_user):
        """Test ending an active session."""
        manager, _, _ = manager_with_user
        
        # Start session
        session_id = manager.start_session("Test", "scope")
        assert manager.state.current_session_id == session_id
        
        # End session
        result = manager.end_session()
        
        assert result is True
        assert manager.state.current_session_id is None
    
    def test_end_session_when_none_active(self, manager_with_user):
        """Test ending session when none is active."""
        manager, _, _ = manager_with_user
        
        result = manager.end_session()
        assert result is False


class TestSessionPersistence:
    """Test session save and delete operations."""
    
    def test_save_current_session(self, manager_with_user):
        """Test saving temporary session as permanent."""
        manager, _, db_path = manager_with_user
        
        # Start temporary session
        session_id = manager.start_session("Temp Session", "scope", temporary=True)
        
        # Save it
        result = manager.save_current_session()
        assert result is True
        
        # Verify in database
        with QueryDB(db_path) as db:
            session = db.get_session(session_id)
            assert session["is_saved"] == 1
    
    def test_save_session_when_none_active(self, manager_with_user):
        """Test saving when no active session."""
        manager, _, _ = manager_with_user
        
        result = manager.save_current_session()
        assert result is False
    
    def test_delete_session_success(self, manager_with_user):
        """Test deleting a session."""
        manager, _, db_path = manager_with_user
        
        # Create session
        session_id = manager.start_session("To Delete", "scope")
        manager.end_session()  # End it first
        
        # Delete it
        result = manager.delete_session(session_id)
        assert result is True
        
        # Verify deleted from database
        with QueryDB(db_path) as db:
            session = db.get_session(session_id)
            assert session is None
    
    def test_delete_current_session_clears_state(self, manager_with_user):
        """Test that deleting current session clears AppState."""
        manager, _, _ = manager_with_user
        
        # Create and keep active
        session_id = manager.start_session("Active Delete", "scope")
        assert manager.state.current_session_id == session_id
        
        # Delete while active
        result = manager.delete_session(session_id)
        
        assert result is True
        assert manager.state.current_session_id is None
    
    def test_delete_nonexistent_session(self, manager_with_user):
        """Test deleting a session that doesn't exist."""
        manager, _, _ = manager_with_user
        
        result = manager.delete_session("nonexistent_id")
        assert result is False
    
    def test_delete_without_auth(self, manager_without_user):
        """Test that deleting without auth raises error."""
        manager = manager_without_user
        
        with pytest.raises(AuthenticationError):
            manager.delete_session("some_id")


class TestSessionResume:
    """Test resuming existing sessions."""
    
    def test_resume_session_success(self, manager_with_user):
        """Test resuming an existing session."""
        manager, _, _ = manager_with_user
        
        # Create and end session
        session_id = manager.start_session("Resume Me", "scope")
        manager.end_session()
        
        # Resume it
        result = manager.resume_session(session_id)
        
        assert result is True
        assert manager.state.current_session_id == session_id
    
    def test_resume_nonexistent_session(self, manager_with_user):
        """Test resuming a session that doesn't exist."""
        manager, _, _ = manager_with_user
        
        result = manager.resume_session("nonexistent_id")
        assert result is False
    
    def test_resume_without_auth(self, manager_without_user):
        """Test that resuming without auth raises error."""
        manager = manager_without_user
        
        with pytest.raises(AuthenticationError):
            manager.resume_session("some_id")
    
    def test_resume_other_users_session(self, temp_db):
        """Test that user cannot resume another user's session."""
        # Create two users
        with QueryDB(temp_db) as db:
            user1_id = db.create_user("user1")
            user2_id = db.create_user("user2")
        
        # User 1 creates a session
        manager1 = SessionManager(db_path=temp_db)
        manager1.state.current_user_id = user1_id
        session_id = manager1.start_session("User1 Session", "scope")
        manager1.end_session()
        
        # User 2 tries to resume it
        manager2 = SessionManager(db_path=temp_db)
        manager2.state.current_user_id = user2_id
        result = manager2.resume_session(session_id)
        
        assert result is False
        assert manager2.state.current_session_id is None
        
        # Cleanup
        manager1.state.clear()
        manager2.state.clear()


class TestListSessions:
    """Test listing user sessions."""
    
    def test_list_sessions_empty(self, manager_with_user):
        """Test listing sessions when user has none."""
        manager, _, _ = manager_with_user
        
        sessions = manager.list_user_sessions()
        assert sessions == []
    
    def test_list_sessions_with_data(self, manager_with_user):
        """Test listing sessions when user has some."""
        manager, _, _ = manager_with_user
        
        # Create multiple sessions
        id1 = manager.start_session("Session 1", "scope1")
        manager.end_session()
        id2 = manager.start_session("Session 2", "scope2")
        manager.end_session()
        
        # List them
        sessions = manager.list_user_sessions()
        
        assert len(sessions) == 2
        session_ids = [s["id"] for s in sessions]
        assert id1 in session_ids
        assert id2 in session_ids
    
    def test_list_sessions_without_auth(self, manager_without_user):
        """Test listing sessions without authentication."""
        manager = manager_without_user
        
        sessions = manager.list_user_sessions()
        assert sessions == []


class TestSecurityIsolation:
    """Test that users can only access their own sessions."""
    
    def test_users_cannot_see_each_others_sessions(self, temp_db):
        """Test that listing sessions is user-specific."""
        # Create two users
        with QueryDB(temp_db) as db:
            user1_id = db.create_user("user1")
            user2_id = db.create_user("user2")
        
        # User 1 creates sessions
        manager1 = SessionManager(db_path=temp_db)
        manager1.state.current_user_id = user1_id
        manager1.start_session("User1 Session 1", "scope")
        manager1.end_session()
        manager1.start_session("User1 Session 2", "scope")
        manager1.end_session()
        
        # User 2 creates sessions
        manager2 = SessionManager(db_path=temp_db)
        manager2.state.current_user_id = user2_id
        manager2.start_session("User2 Session", "scope")
        manager2.end_session()
        
        # Each user should only see their own
        # Note: AppState is a singleton, so we need to set current_user_id before each call
        manager1.state.current_user_id = user1_id
        user1_sessions = manager1.list_user_sessions()
        
        manager2.state.current_user_id = user2_id
        user2_sessions = manager2.list_user_sessions()
        
        assert len(user1_sessions) == 2
        assert len(user2_sessions) == 1
        
        # Cleanup
        manager1.state.clear()
        manager2.state.clear()
    
    def test_user_cannot_delete_other_users_session(self, temp_db):
        """Test that user cannot delete another user's session."""
        # Create two users
        with QueryDB(temp_db) as db:
            user1_id = db.create_user("user1")
            user2_id = db.create_user("user2")
        
        # User 1 creates a session
        manager1 = SessionManager(db_path=temp_db)
        manager1.state.current_user_id = user1_id
        session_id = manager1.start_session("Protected Session", "scope")
        manager1.end_session()
        
        # User 2 tries to delete it
        manager2 = SessionManager(db_path=temp_db)
        manager2.state.current_user_id = user2_id
        result = manager2.delete_session(session_id)
        
        assert result is False
        
        # Verify session still exists
        with QueryDB(temp_db) as db:
            session = db.get_session(session_id)
            assert session is not None
        
        # Cleanup
        manager1.state.clear()
        manager2.state.clear()
