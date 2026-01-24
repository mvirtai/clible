"""
Tests for AnalysisTracker class.

Tests cover:
- Saving word frequency analysis
- Saving phrase analysis  
- Retrieving analysis history
- Retrieving specific analysis results
- Comparing analyses
- Edge cases and error handling
"""

import pytest
import json
from pathlib import Path
import tempfile

from app.analytics.analysis_tracker import AnalysisTracker
from app.state import AppState
from app.db.queries import QueryDB

### FIXTURES
@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_clible.db"

    # Initialize database with tables
    with QueryDB(db_path) as db:
        pass # Tables are created automatically

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def tracker_with_user(temp_db):
    """
    Create an AnalysisTracker with a logged-in user.
    
    Returns tuple: (tracker, user_id, db_path)
    """
    # Create user in database
    with QueryDB(temp_db) as db:
        user_id = db.create_user("test_user")
    
    # Create tracker with user AND db_path
    state = AppState()
    state.current_user_id = user_id
    
    tracker = AnalysisTracker(
        user_id=user_id,
        session_id=None,
        db_path=temp_db,
    )
    
    yield tracker, user_id, temp_db
    
    # Cleanup
    state.clear()


@pytest.fixture
def sample_word_freq():
    """Sample word frequency data for testing."""
    return [
        ("jesus", 120),
        ("lord", 85),
        ("god", 65),
        ("love", 45),
        ("faith", 30)
    ]


@pytest.fixture
def sample_vocab_info():
    """Sample vocabulary info for testing."""
    return {
        "total_tokens": 1500,
        "vocabulary_size": 450,
        "type_token_ratio": 0.3
    }


@pytest.fixture
def sample_bigrams():
    """Sample bigram data for testing."""
    return [
        ("love god", 45),
        ("holy spirit", 32),
        ("jesus christ", 28),
        ("believe in", 22),
        ("kingdom of", 18)
    ]


@pytest.fixture
def sample_trigrams():
    """Sample trigram data for testing."""
    return [
        ("in the beginning", 15),
        ("son of god", 12),
        ("kingdom of heaven", 10),
        ("fear not for", 8),
        ("thus saith the", 7)
    ]


############################
# TESTS
############################

class TestSaveWordFrequencyAnalysis:
    """Test saving word frequency analysis to database."""

    def test_save_creates_analysis_id(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test that saving analysis returns a valid analysis ID."""
        tracker, user_id, db_path = tracker_with_user

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "test_query_123"},
            verse_count=25
        )

        assert analysis_id is not None
        assert len(analysis_id) == 8  # UUID hex[:8]
    
    def test_save_creates_history_record(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test that analysis history record is created with correct metadata."""
        tracker, user_id, db_path = tracker_with_user

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "test_query_123"},
            verse_count=25
        )

        # Verify in database
        with QueryDB(db_path) as db:
            db.cur.execute(
                "SELECT * FROM analysis_history WHERE id = ?",
                (analysis_id,)
            )
            history = db.cur.fetchone()

        assert history is not None
        assert history["user_id"] == user_id
        assert history["analysis_type"] == "word_frequency"
        assert history["scope_type"] == "query"
        assert history["verse_count"] == 25
        assert history["created_at"] is not None
        
        # Check user_name is stored (new feature)
        # Get user name from database to verify
        with QueryDB(db_path) as db:
            user = db.get_user_by_id(user_id)
            if user:
                assert history["user_name"] == user["name"]
            else:
                assert history["user_name"] == "Unknown"

        # Check scope_details is valid JSON
        scope_details = json.loads(history["scope_details"])
        assert scope_details["query_id"] == "test_query_123"
    
    def test_save_creates_two_result_records(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test that two result records are created (word_freq + vocab_stats)."""
        tracker, user_id, db_path = tracker_with_user

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "test_query_123"},
            verse_count=25
        )

        # Verify in database
        with QueryDB(db_path) as db:
            db.cur.execute(
                "SELECT * FROM analysis_results WHERE analysis_id = ?",
                (analysis_id,)
            )
            results = db.cur.fetchall()

        assert len(results) == 2

        # Check result types
        result_types = {r["result_type"] for r in results}
        assert result_types == {"word_freq", "vocab_stats"}
    
    def test_word_freq_data_is_valid_json(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test that word frequency data is properly serialized as JSON."""
        tracker, user_id, db_path = tracker_with_user

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "test_query_123"},
            verse_count=25
        )

        with QueryDB(db_path) as db:
            db.cur.execute(
                "SELECT result_data FROM analysis_results WHERE analysis_id = ? AND result_type = 'word_freq'",
                (analysis_id,)
            )
            result = db.cur.fetchone()

        # Parse JSON
        word_freq_data = json.loads(result["result_data"])

        assert isinstance(word_freq_data, list)
        assert len(word_freq_data) == 5
        assert word_freq_data[0][0] == "jesus"
        assert word_freq_data[0][1] == 120
    
    def test_vocab_stats_data_is_valid_json(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test that vocabulary statistics are properly serialized as JSON."""
        tracker, user_id, db_path = tracker_with_user

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "test_query_123"},
            verse_count=25
        )

        with QueryDB(db_path) as db:
            db.cur.execute(
                "SELECT result_data FROM analysis_results WHERE analysis_id = ? AND result_type = 'vocab_stats'",
                (analysis_id,)
            )
            result = db.cur.fetchone()

        # Parse JSON
        vocab_data = json.loads(result["result_data"])

        assert vocab_data["total_tokens"] == 1500
        assert vocab_data["vocabulary_size"] == 450
        assert vocab_data["type_token_ratio"] == 0.3
    
    def test_save_with_session_id(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test saving analysis within a session context."""
        tracker, user_id, db_path = tracker_with_user
        
        # Create a session
        with QueryDB(db_path) as db:
            session_id = db.create_session(user_id, "Test Session", "John 1-3", is_temporary=False)
        
        # Update tracker with session
        tracker.session_id = session_id

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="session",
            scope_details={"session_id": session_id},
            verse_count=25
        )

        # Verify session_id is stored
        with QueryDB(db_path) as db:
            db.cur.execute(
                "SELECT session_id FROM analysis_history WHERE id = ?",
                (analysis_id,)
            )
            result = db.cur.fetchone()
        
        assert result["session_id"] == session_id
    
    def test_save_with_chart_paths(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test saving analysis with visualization chart paths."""
        tracker, user_id, db_path = tracker_with_user

        chart_paths = {
            "word_freq": "data/charts/word_frequency/2025-01-01_12-00-00_word_freq.png",
            "vocab_stats": "data/charts/word_frequency/2025-01-01_12-00-01_vocab_stats.png"
        }

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "test_query_123"},
            verse_count=25,
            chart_paths=chart_paths
        )

        # Verify chart paths are stored
        with QueryDB(db_path) as db:
            db.cur.execute(
                "SELECT result_type, chart_path FROM analysis_results WHERE analysis_id = ?",
                (analysis_id,)
            )
            results = db.cur.fetchall()
        
        chart_paths_stored = {r["result_type"]: r["chart_path"] for r in results}
        assert chart_paths_stored["word_freq"] == chart_paths["word_freq"]
        assert chart_paths_stored["vocab_stats"] == chart_paths["vocab_stats"]
    
    def test_save_with_different_scope_types(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test saving analyses with different scope types (query, session, book, multi_query)."""
        tracker, user_id, db_path = tracker_with_user

        scope_configs = [
            ("query", {"query_id": "abc123"}),
            ("session", {"session_id": "def456"}),
            ("book", {"book": "John"}),
            ("multi_query", {"query_ids": ["abc", "def", "ghi"]})
        ]

        analysis_ids = []
        for scope_type, scope_details in scope_configs:
            analysis_id = tracker.save_word_frequency_analysis(
                word_freq=sample_word_freq,
                vocab_info=sample_vocab_info,
                scope_type=scope_type,
                scope_details=scope_details,
                verse_count=25
            )
            analysis_ids.append(analysis_id)

        # Verify all were saved with correct scope types
        with QueryDB(db_path) as db:
            for idx, (scope_type, _) in enumerate(scope_configs):
                db.cur.execute(
                    "SELECT scope_type FROM analysis_history WHERE id = ?",
                    (analysis_ids[idx],)
                )
                result = db.cur.fetchone()
                assert result["scope_type"] == scope_type


class TestSavePhraseAnalysis:
    """Test saving phrase analysis (bigrams and trigrams) to database."""

    def test_save_phrase_creates_analysis_id(self, tracker_with_user, sample_bigrams, sample_trigrams):
        """Test that saving phrase analysis returns a valid analysis ID."""
        tracker, user_id, db_path = tracker_with_user

        analysis_id = tracker.save_phrase_analysis(
            bigrams=sample_bigrams,
            trigrams=sample_trigrams,
            scope_type="query",
            scope_details={"query_id": "test_query_456"},
            verse_count=30
        )

        assert analysis_id is not None
        assert len(analysis_id) == 8
    
    def test_save_phrase_creates_history_record(self, tracker_with_user, sample_bigrams, sample_trigrams):
        """Test that phrase analysis history record is created correctly."""
        tracker, user_id, db_path = tracker_with_user

        analysis_id = tracker.save_phrase_analysis(
            bigrams=sample_bigrams,
            trigrams=sample_trigrams,
            scope_type="query",
            scope_details={"query_id": "test_query_456"},
            verse_count=30
        )

        with QueryDB(db_path) as db:
            db.cur.execute(
                "SELECT * FROM analysis_history WHERE id = ?",
                (analysis_id,)
            )
            history = db.cur.fetchone()

        assert history is not None
        assert history["user_id"] == user_id
        assert history["analysis_type"] == "phrase_analysis"
        assert history["scope_type"] == "query"
        assert history["verse_count"] == 30
        
        # Check user_name is stored (new feature)
        # Get user name from database to verify
        with QueryDB(db_path) as db:
            user = db.get_user_by_id(user_id)
            if user:
                assert history["user_name"] == user["name"]
            else:
                assert history["user_name"] == "Unknown"
    
    def test_save_phrase_creates_two_result_records(self, tracker_with_user, sample_bigrams, sample_trigrams):
        """Test that two result records are created (bigram + trigram)."""
        tracker, user_id, db_path = tracker_with_user

        analysis_id = tracker.save_phrase_analysis(
            bigrams=sample_bigrams,
            trigrams=sample_trigrams,
            scope_type="query",
            scope_details={"query_id": "test_query_456"},
            verse_count=30
        )

        with QueryDB(db_path) as db:
            db.cur.execute(
                "SELECT * FROM analysis_results WHERE analysis_id = ?",
                (analysis_id,)
            )
            results = db.cur.fetchall()

        assert len(results) == 2

        result_types = {r["result_type"] for r in results}
        assert result_types == {"bigram", "trigram"}
    
    def test_bigram_data_is_valid_json(self, tracker_with_user, sample_bigrams, sample_trigrams):
        """Test that bigram data is properly serialized as JSON."""
        tracker, user_id, db_path = tracker_with_user

        analysis_id = tracker.save_phrase_analysis(
            bigrams=sample_bigrams,
            trigrams=sample_trigrams,
            scope_type="query",
            scope_details={"query_id": "test_query_456"},
            verse_count=30
        )

        with QueryDB(db_path) as db:
            db.cur.execute(
                "SELECT result_data FROM analysis_results WHERE analysis_id = ? AND result_type = 'bigram'",
                (analysis_id,)
            )
            result = db.cur.fetchone()

        bigram_data = json.loads(result["result_data"])

        assert isinstance(bigram_data, list)
        assert len(bigram_data) == 5
        assert bigram_data[0][0] == "love god"
        assert bigram_data[0][1] == 45
    
    def test_trigram_data_is_valid_json(self, tracker_with_user, sample_bigrams, sample_trigrams):
        """Test that trigram data is properly serialized as JSON."""
        tracker, user_id, db_path = tracker_with_user

        analysis_id = tracker.save_phrase_analysis(
            bigrams=sample_bigrams,
            trigrams=sample_trigrams,
            scope_type="query",
            scope_details={"query_id": "test_query_456"},
            verse_count=30
        )

        with QueryDB(db_path) as db:
            db.cur.execute(
                "SELECT result_data FROM analysis_results WHERE analysis_id = ? AND result_type = 'trigram'",
                (analysis_id,)
            )
            result = db.cur.fetchone()

        trigram_data = json.loads(result["result_data"])

        assert isinstance(trigram_data, list)
        assert len(trigram_data) == 5
        assert trigram_data[0][0] == "in the beginning"
        assert trigram_data[0][1] == 15


class TestGetAnalysisHistory:
    """Test retrieving analysis history with filtering options."""

    def test_get_history_returns_all_analyses(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test retrieving all analyses for a user."""
        tracker, user_id, db_path = tracker_with_user

        # Create multiple analyses
        for i in range(3):
            tracker.save_word_frequency_analysis(
                word_freq=sample_word_freq,
                vocab_info=sample_vocab_info,
                scope_type="query",
                scope_details={"query_id": f"query_{i}"},
                verse_count=25 + i
            )

        history = tracker.get_analysis_history(limit=10)

        assert len(history) == 3
        assert all("id" in h for h in history)
        assert all("analysis_type" in h for h in history)
        assert all("created_at" in h for h in history)
    
    def test_get_history_respects_limit(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test that limit parameter correctly restricts results."""
        tracker, user_id, db_path = tracker_with_user

        # Create 5 analyses
        for i in range(5):
            tracker.save_word_frequency_analysis(
                word_freq=sample_word_freq,
                vocab_info=sample_vocab_info,
                scope_type="query",
                scope_details={"query_id": f"query_{i}"},
                verse_count=25
            )

        history = tracker.get_analysis_history(limit=3)

        assert len(history) == 3
    
    def test_get_history_filters_by_analysis_type(self, tracker_with_user, sample_word_freq, 
                                                    sample_vocab_info, sample_bigrams, sample_trigrams):
        """Test filtering history by analysis type."""
        tracker, user_id, db_path = tracker_with_user

        # Create mixed analyses
        tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "query_1"},
            verse_count=25
        )
        tracker.save_phrase_analysis(
            bigrams=sample_bigrams,
            trigrams=sample_trigrams,
            scope_type="query",
            scope_details={"query_id": "query_2"},
            verse_count=30
        )
        tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "query_3"},
            verse_count=25
        )

        # Filter by word_frequency
        history = tracker.get_analysis_history(analysis_type="word_frequency")

        assert len(history) == 2
        assert all(h["analysis_type"] == "word_frequency" for h in history)
    
    def test_get_history_filters_by_scope_type(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test filtering history by scope type."""
        tracker, user_id, db_path = tracker_with_user

        # Create analyses with different scopes
        tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "query_1"},
            verse_count=25
        )
        tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="book",
            scope_details={"book": "John"},
            verse_count=50
        )

        # Filter by scope
        history = tracker.get_analysis_history(scope_type="book")

        assert len(history) == 1
        assert history[0]["scope_type"] == "book"
    
    def test_get_history_returns_most_recent_first(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test that history is ordered by creation time (most recent first)."""
        tracker, user_id, db_path = tracker_with_user

        # Create analyses with distinct verse counts
        id1 = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "first"},
            verse_count=10
        )
        id2 = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "second"},
            verse_count=20
        )
        id3 = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "third"},
            verse_count=30
        )

        history = tracker.get_analysis_history()

        # Most recent (id3) should be first
        assert history[0]["id"] == id3
        assert history[1]["id"] == id2
        assert history[2]["id"] == id1
    
    def test_get_history_filters_by_session_id(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test filtering history by session_id."""
        tracker, user_id, db_path = tracker_with_user

        # Create two sessions
        with QueryDB(db_path) as db:
            session_1 = db.create_session(user_id, "Session 1", "John 1-3", is_temporary=False)
            session_2 = db.create_session(user_id, "Session 2", "Romans 1-3", is_temporary=False)

        # Create analyses in different sessions
        tracker.session_id = session_1
        id1 = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="session",
            scope_details={"session_id": session_1},
            verse_count=25
        )
        id2 = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="session",
            scope_details={"session_id": session_1},
            verse_count=30
        )

        tracker.session_id = session_2
        id3 = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="session",
            scope_details={"session_id": session_2},
            verse_count=35
        )

        # Filter by session_1
        history = tracker.get_analysis_history(session_id=session_1)

        assert len(history) == 2
        assert all(h["session_id"] == session_1 for h in history)
        assert id1 in [h["id"] for h in history]
        assert id2 in [h["id"] for h in history]
        assert id3 not in [h["id"] for h in history]
    
    def test_get_history_filters_by_session_id_with_other_filters(self, tracker_with_user, sample_word_freq, 
                                                                   sample_vocab_info, sample_bigrams, sample_trigrams):
        """Test that session_id filter works in combination with other filters."""
        tracker, user_id, db_path = tracker_with_user

        # Create session
        with QueryDB(db_path) as db:
            session_1 = db.create_session(user_id, "Session 1", "John 1-3", is_temporary=False)

        tracker.session_id = session_1

        # Create mixed analyses in session_1
        tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="session",
            scope_details={"session_id": session_1},
            verse_count=25
        )
        tracker.save_phrase_analysis(
            bigrams=sample_bigrams,
            trigrams=sample_trigrams,
            scope_type="session",
            scope_details={"session_id": session_1},
            verse_count=30
        )
        tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="session",
            scope_details={"session_id": session_1},
            verse_count=35
        )

        # Filter by session AND analysis_type
        history = tracker.get_analysis_history(
            session_id=session_1,
            analysis_type="word_frequency"
        )

        assert len(history) == 2
        assert all(h["session_id"] == session_1 for h in history)
        assert all(h["analysis_type"] == "word_frequency" for h in history)
    
    def test_get_history_with_none_session_id_returns_all(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test that passing None as session_id returns analyses from all sessions."""
        tracker, user_id, db_path = tracker_with_user

        # Create two sessions
        with QueryDB(db_path) as db:
            session_1 = db.create_session(user_id, "Session 1", "John 1-3", is_temporary=False)
            session_2 = db.create_session(user_id, "Session 2", "Romans 1-3", is_temporary=False)

        # Create analyses in different sessions
        tracker.session_id = session_1
        tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="session",
            scope_details={"session_id": session_1},
            verse_count=25
        )

        tracker.session_id = session_2
        tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="session",
            scope_details={"session_id": session_2},
            verse_count=30
        )

        # Get all analyses (no session filter)
        history_all = tracker.get_analysis_history(session_id=None)
        assert len(history_all) == 2

        # Get analyses from session_1 only
        history_session1 = tracker.get_analysis_history(session_id=session_1)
        assert len(history_session1) == 1
        assert history_session1[0]["session_id"] == session_1
    
    def test_get_history_with_empty_session_returns_nothing(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test that filtering by non-existent session_id returns empty list."""
        tracker, user_id, db_path = tracker_with_user

        # Create analysis without session
        tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "test"},
            verse_count=25
        )

        # Filter by non-existent session
        history = tracker.get_analysis_history(session_id="nonexistent_session")

        assert len(history) == 0


class TestGetAnalysisResults:
    """Test retrieving specific analysis results by ID."""

    def test_get_results_returns_complete_analysis(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test retrieving complete analysis with metadata and results."""
        tracker, user_id, db_path = tracker_with_user

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "test_query_123"},
            verse_count=25
        )

        results = tracker.get_analysis_results(analysis_id)

        # Check metadata
        assert results["id"] == analysis_id
        assert results["analysis_type"] == "word_frequency"
        assert results["scope_type"] == "query"
        assert results["verse_count"] == 25
        assert "created_at" in results

        # Check results data
        assert "results" in results
        assert "word_freq" in results["results"]
        assert "vocab_stats" in results["results"]
    
    def test_get_results_deserializes_json_data(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test that JSON data is properly deserialized into Python objects."""
        tracker, user_id, db_path = tracker_with_user

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "test_query_123"},
            verse_count=25
        )

        results = tracker.get_analysis_results(analysis_id)

        # Check word_freq is a list of lists (not JSON string)
        word_freq_data = results["results"]["word_freq"]
        assert isinstance(word_freq_data, list)
        assert word_freq_data[0][0] == "jesus"
        assert word_freq_data[0][1] == 120

        # Check vocab_stats is a dict (not JSON string)
        vocab_data = results["results"]["vocab_stats"]
        assert isinstance(vocab_data, dict)
        assert vocab_data["total_tokens"] == 1500
    
    def test_get_results_returns_none_for_invalid_id(self, tracker_with_user):
        """Test that getting non-existent analysis returns None."""
        tracker, user_id, db_path = tracker_with_user

        results = tracker.get_analysis_results("nonexistent_id")

        assert results is None
    
    def test_get_results_includes_chart_paths(self, tracker_with_user, sample_word_freq, sample_vocab_info):
        """Test that chart paths are included in results when available."""
        tracker, user_id, db_path = tracker_with_user

        chart_paths = {
            "word_freq": "data/charts/test.png",
            "vocab_stats": "data/charts/test2.png"
        }

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "test_query_123"},
            verse_count=25,
            chart_paths=chart_paths
        )

        results = tracker.get_analysis_results(analysis_id)

        assert "chart_paths" in results
        assert results["chart_paths"]["word_freq"] == chart_paths["word_freq"]
        assert results["chart_paths"]["vocab_stats"] == chart_paths["vocab_stats"]




class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_save_with_empty_word_freq(self, tracker_with_user, sample_vocab_info):
        """Test handling of empty word frequency list."""
        tracker, user_id, db_path = tracker_with_user

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=[],
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "empty_test"},
            verse_count=0
        )

        assert analysis_id is not None
        
        # Verify empty list is stored
        with QueryDB(db_path) as db:
            db.cur.execute(
                "SELECT result_data FROM analysis_results WHERE analysis_id = ? AND result_type = 'word_freq'",
                (analysis_id,)
            )
            result = db.cur.fetchone()
        
        data = json.loads(result["result_data"])
        assert data == []
    
    def test_save_without_user_id(self, temp_db, sample_word_freq, sample_vocab_info):
        """Test saving analysis without authenticated user (user_id = None)."""
        tracker = AnalysisTracker(user_id=None, session_id=None, db_path=temp_db)

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=sample_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "test"},
            verse_count=25
        )

        # Should still work, with NULL user_id but "Unknown" user_name
        assert analysis_id is not None
        
        with QueryDB(temp_db) as db:
            db.cur.execute(
                "SELECT user_id, user_name FROM analysis_history WHERE id = ?",
                (analysis_id,)
            )
            result = db.cur.fetchone()
        
        assert result["user_id"] is None
        # user_name should be "Unknown" due to NOT NULL constraint
        assert result["user_name"] == "Unknown"
    
    def test_save_with_large_dataset(self, tracker_with_user, sample_vocab_info):
        """Test saving analysis with very large word frequency list."""
        tracker, user_id, db_path = tracker_with_user

        # Create large dataset (1000 words)
        large_word_freq = [(f"word_{i}", 100 - i) for i in range(1000)]

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=large_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "large_test"},
            verse_count=5000
        )

        assert analysis_id is not None
        
        # Verify data integrity
        with QueryDB(db_path) as db:
            db.cur.execute(
                "SELECT result_data FROM analysis_results WHERE analysis_id = ? AND result_type = 'word_freq'",
                (analysis_id,)
            )
            result = db.cur.fetchone()
        
        data = json.loads(result["result_data"])
        assert len(data) == 1000
        assert data[0][0] == "word_0"
        assert data[999][0] == "word_999"
    
    def test_save_with_special_characters_in_words(self, tracker_with_user, sample_vocab_info):
        """Test handling of special characters in word data."""
        tracker, user_id, db_path = tracker_with_user

        special_word_freq = [
            ("god's", 50),
            ("can't", 40),
            ("jesus'", 30),
            ("re-establish", 20),
            ("über", 10)  # Unicode character
        ]

        analysis_id = tracker.save_word_frequency_analysis(
            word_freq=special_word_freq,
            vocab_info=sample_vocab_info,
            scope_type="query",
            scope_details={"query_id": "special_chars"},
            verse_count=25
        )

        assert analysis_id is not None
        
        # Verify special characters preserved
        with QueryDB(db_path) as db:
            db.cur.execute(
                "SELECT result_data FROM analysis_results WHERE analysis_id = ? AND result_type = 'word_freq'",
                (analysis_id,)
            )
            result = db.cur.fetchone()
        
        data = json.loads(result["result_data"])
        words = [w[0] for w in data]
        assert "god's" in words
        assert "can't" in words
        assert "über" in words