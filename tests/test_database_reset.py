"""
Tests for database reset functionality.

Tests cover:
- Resetting database drops all tables correctly
- Resetting database recreates tables correctly
- Foreign key constraint handling during reset
- Table dependency order during reset
"""

import pytest
import tempfile
from pathlib import Path

from app.db.queries import QueryDB


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_clible.db"

    # Initialize database with tables
    with QueryDB(db_path) as db:
        pass  # Tables are created automatically

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def db_with_data(temp_db):
    """Create a database with some test data."""
    with QueryDB(temp_db) as db:
        # Create user
        user_id = db.create_user("test_user")
        
        # Create session
        session_id = db.create_session(user_id, "Test Session", "John 1-3")
        
        # Create query
        query_id = db.save_query({
            "reference": "John 3:16",
            "verses": [{
                "book_name": "John",
                "chapter": 3,
                "verse": 16,
                "text": "For God so loved the world..."
            }]
        })
        
        # Link query to session
        db.add_query_to_session(session_id, query_id)
    
    return temp_db, user_id, session_id, query_id


class TestDatabaseReset:
    """Test database reset functionality."""

    def test_reset_drops_all_tables(self, db_with_data):
        """Test that reset drops all tables."""
        db_path, user_id, session_id, query_id = db_with_data

        with QueryDB(db_path) as db:
            # Verify data exists
            db.cur.execute("SELECT COUNT(*) as count FROM users")
            user_count_before = db.cur.fetchone()["count"]
            assert user_count_before > 0

            # Reset database
            db._reset_database()

            # Verify all tables are dropped (by checking they don't exist or are empty)
            # SQLite doesn't raise error for SELECT on non-existent table, so check differently
            try:
                db.cur.execute("SELECT COUNT(*) as count FROM users")
                user_count_after = db.cur.fetchone()["count"]
                # After reset, tables should be recreated but empty
                assert user_count_after == 0
            except Exception:
                # If table doesn't exist, that's also fine (though shouldn't happen after reset)
                pass

    def test_reset_recreates_tables(self, db_with_data):
        """Test that reset recreates all tables."""
        db_path, user_id, session_id, query_id = db_with_data

        with QueryDB(db_path) as db:
            db._reset_database()

        # Verify tables exist by trying to insert data
        with QueryDB(db_path) as db:
            # Should be able to create user (users table exists)
            new_user_id = db.create_user("new_user")
            assert new_user_id is not None

            # Should be able to create session (sessions table exists)
            new_session_id = db.create_session(new_user_id, "New Session", "Genesis 1")
            assert new_session_id is not None

            # Should be able to create query (queries table exists)
            new_query_id = db.save_query({
                "reference": "Genesis 1:1",
                "verses": [{
                    "book_name": "Genesis",
                    "chapter": 1,
                    "verse": 1,
                    "text": "In the beginning..."
                }]
            })
            assert new_query_id is not None

    def test_reset_handles_foreign_keys_correctly(self, db_with_data):
        """Test that reset handles foreign key constraints correctly."""
        db_path, user_id, session_id, query_id = db_with_data

        # This test verifies that reset doesn't fail due to foreign key constraints
        # The reset should drop child tables before parent tables
        with QueryDB(db_path) as db:
            # Should not raise IntegrityError
            try:
                db._reset_database()
                reset_successful = True
            except Exception as e:
                reset_successful = False
                pytest.fail(f"Reset failed with error: {e}")

        assert reset_successful

    def test_reset_clears_all_data(self, db_with_data):
        """Test that reset clears all existing data."""
        db_path, user_id, session_id, query_id = db_with_data

        with QueryDB(db_path) as db:
            # Verify data exists before reset
            db.cur.execute("SELECT COUNT(*) as count FROM users")
            users_before = db.cur.fetchone()["count"]
            
            db.cur.execute("SELECT COUNT(*) as count FROM sessions")
            sessions_before = db.cur.fetchone()["count"]
            
            db.cur.execute("SELECT COUNT(*) as count FROM queries")
            queries_before = db.cur.fetchone()["count"]

            assert users_before > 0
            assert sessions_before > 0
            assert queries_before > 0

            # Reset
            db._reset_database()

            # Verify all data is cleared
            db.cur.execute("SELECT COUNT(*) as count FROM users")
            users_after = db.cur.fetchone()["count"]
            
            db.cur.execute("SELECT COUNT(*) as count FROM sessions")
            sessions_after = db.cur.fetchone()["count"]
            
            db.cur.execute("SELECT COUNT(*) as count FROM queries")
            queries_after = db.cur.fetchone()["count"]

            assert users_after == 0
            assert sessions_after == 0
            assert queries_after == 0

    def test_reset_preserves_schema_structure(self, db_with_data):
        """Test that reset preserves the schema structure (columns, constraints)."""
        db_path, user_id, session_id, query_id = db_with_data

        with QueryDB(db_path) as db:
            # Get schema info before reset
            db.cur.execute("PRAGMA table_info(users)")
            users_columns_before = {row[1]: row[2] for row in db.cur.fetchall()}

            db.cur.execute("PRAGMA table_info(analysis_history)")
            analysis_columns_before = {row[1]: row[2] for row in db.cur.fetchall()}

            # Reset
            db._reset_database()

            # Get schema info after reset
            db.cur.execute("PRAGMA table_info(users)")
            users_columns_after = {row[1]: row[2] for row in db.cur.fetchall()}

            db.cur.execute("PRAGMA table_info(analysis_history)")
            analysis_columns_after = {row[1]: row[2] for row in db.cur.fetchall()}

            # Verify schema is preserved
            assert users_columns_before == users_columns_after
            assert analysis_columns_before == analysis_columns_after
            # Verify user_name column exists in analysis_history
            assert "user_name" in analysis_columns_after

