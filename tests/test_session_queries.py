"""
Tests for session-query linking functionality.

Tests cover:
- add_query_to_session() bug fix
- Linking queries to sessions
- Handling duplicate links
- Edge cases
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
def db_with_user_and_session(temp_db):
    """Create a database with a user and session."""
    with QueryDB(temp_db) as db:
        user_id = db.create_user("test_user")
        session_id = db.create_session(user_id, "Test Session", "John 1-3")
    
    return temp_db, user_id, session_id


@pytest.fixture
def sample_query_data():
    """Sample query data for testing."""
    return {
        "reference": "John 3:16",
        "verses": [{
            "book_name": "John",
            "chapter": 3,
            "verse": 16,
            "text": "For God so loved the world..."
        }]
    }


class TestAddQueryToSession:
    """Test add_query_to_session functionality."""

    def test_add_query_to_session_links_correctly(self, db_with_user_and_session, sample_query_data):
        """Test that add_query_to_session correctly links query to session."""
        db_path, user_id, session_id = db_with_user_and_session

        with QueryDB(db_path) as db:
            # Create query
            query_id = db.save_query(sample_query_data)

            # Link query to session
            db.add_query_to_session(session_id, query_id)

            # Verify link exists
            db.cur.execute(
                "SELECT * FROM session_queries WHERE session_id = ? AND query_id = ?",
                (session_id, query_id)
            )
            result = db.cur.fetchone()

            assert result is not None
            assert result["session_id"] == session_id
            assert result["query_id"] == query_id

    def test_add_query_to_session_handles_duplicate_gracefully(self, db_with_user_and_session, sample_query_data):
        """Test that adding the same query twice doesn't raise error."""
        db_path, user_id, session_id = db_with_user_and_session

        with QueryDB(db_path) as db:
            # Create query
            query_id = db.save_query(sample_query_data)

            # Link query to session (first time)
            db.add_query_to_session(session_id, query_id)

            # Link again (should not raise error)
            db.add_query_to_session(session_id, query_id)

            # Verify only one link exists
            db.cur.execute(
                "SELECT COUNT(*) as count FROM session_queries WHERE session_id = ? AND query_id = ?",
                (session_id, query_id)
            )
            result = db.cur.fetchone()

            assert result["count"] == 1

    def test_add_query_to_session_with_none_session_id(self, db_with_user_and_session, sample_query_data):
        """Test that None session_id is handled gracefully."""
        db_path, user_id, session_id = db_with_user_and_session

        with QueryDB(db_path) as db:
            query_id = db.save_query(sample_query_data)

            # Should not raise error
            db.add_query_to_session(None, query_id)

            # Verify no link was created
            db.cur.execute(
                "SELECT COUNT(*) as count FROM session_queries WHERE query_id = ?",
                (query_id,)
            )
            result = db.cur.fetchone()

            assert result["count"] == 0

    def test_add_query_to_session_with_none_query_id(self, db_with_user_and_session):
        """Test that None query_id is handled gracefully."""
        db_path, user_id, session_id = db_with_user_and_session

        with QueryDB(db_path) as db:
            # Should not raise error
            db.add_query_to_session(session_id, None)

            # Verify no link was created
            db.cur.execute(
                "SELECT COUNT(*) as count FROM session_queries WHERE session_id = ?",
                (session_id,)
            )
            result = db.cur.fetchone()

            assert result["count"] == 0

    def test_add_query_to_session_with_invalid_session_id(self, db_with_user_and_session, sample_query_data):
        """Test that invalid session_id is handled gracefully (silently fails)."""
        db_path, user_id, session_id = db_with_user_and_session

        with QueryDB(db_path) as db:
            query_id = db.save_query(sample_query_data)

            # Should not raise exception (handled silently), but no link should be created
            db.add_query_to_session("invalid_session_id", query_id)

            # Verify no link was created
            db.cur.execute(
                "SELECT COUNT(*) as count FROM session_queries WHERE query_id = ?",
                (query_id,)
            )
            result = db.cur.fetchone()

            assert result["count"] == 0

    def test_add_query_to_session_with_invalid_query_id(self, db_with_user_and_session):
        """Test that invalid query_id is handled gracefully (silently fails)."""
        db_path, user_id, session_id = db_with_user_and_session

        with QueryDB(db_path) as db:
            # Should not raise exception (handled silently), but no link should be created
            db.add_query_to_session(session_id, "invalid_query_id")

            # Verify no link was created
            db.cur.execute(
                "SELECT COUNT(*) as count FROM session_queries WHERE session_id = ?",
                (session_id,)
            )
            result = db.cur.fetchone()

            assert result["count"] == 0

    def test_add_multiple_queries_to_session(self, db_with_user_and_session):
        """Test adding multiple queries to the same session."""
        db_path, user_id, session_id = db_with_user_and_session

        query_ids = []
        with QueryDB(db_path) as db:
            # Create multiple queries
            for i in range(3):
                query_data = {
                    "reference": f"John {i+1}:{i+1}",
                    "verses": [{
                        "book_name": "John",
                        "chapter": i+1,
                        "verse": i+1,
                        "text": f"Verse {i+1} text..."
                    }]
                }
                query_id = db.save_query(query_data)
                query_ids.append(query_id)

                # Link to session
                db.add_query_to_session(session_id, query_id)

            # Verify all links exist
            db.cur.execute(
                "SELECT COUNT(*) as count FROM session_queries WHERE session_id = ?",
                (session_id,)
            )
            result = db.cur.fetchone()

            assert result["count"] == 3

            # Verify each query is linked
            db.cur.execute(
                "SELECT query_id FROM session_queries WHERE session_id = ? ORDER BY query_id",
                (session_id,)
            )
            linked_query_ids = [row["query_id"] for row in db.cur.fetchall()]

            assert set(linked_query_ids) == set(query_ids)

