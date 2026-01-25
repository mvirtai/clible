"""
Session management module.

Provides SessionManager class for handling user sessions,
coordinating between AppState (in-memory state) and QueryDB (persistence).
"""

from loguru import logger

from app.db.queries import QueryDB
from app.state import AppState


class AuthenticationError(Exception):
    """Exception raised when authentication is required but not provided."""
    pass


class SessionManager:
    """
    Manages user sessions by coordinating AppState and database operations.

    Responsibilities:
    - Provide high-level session operations (start, resume, save, delete)
    - Keep AppState synchronized with database
    - Validate operations before executing them
    - Handle errors gracefully

    The SessionManager does NOT store state itself - it manages the state
    stored in AppState singleton.
    """

    def __init__(self, db_path=None):
        """
        Initialize SessionManager with reference to AppState singleton.

        Args:
            db_path: Optional path to database file (for testing)
        """
        self.state = AppState()
        self.db_path = db_path

    def _get_db(self):
        """
        Get QueryDB instance with appropriate db_path.

        If db_path is None, uses the default DB_PATH from QueryDB.
        If db_path is set (e.g., for testing), uses that path.
        """
        if self.db_path is None:
            return QueryDB()
        return QueryDB(self.db_path)

    def start_session(self, name: str, scope: str, temporary: bool = False) -> str | None:
        """Create a new temporary session and set it as current session."""
        if not self.state.is_authenticated:
            raise AuthenticationError("User must be logged in to start a session.")

        with self._get_db() as db:
            session_id = db.create_session(
                user_id=self.state.current_user_id,
                name=name,
                scope=scope,
                is_temporary=temporary,
            )

        if not session_id:
            logger.error("Failed to create session.")
            return None

        logger.info(f"Session started successfully with ID: {session_id}")
        self.state.current_session_id = session_id
        return session_id

    def end_session(self) -> bool:
        """
        End current session, keeping data in cache.

        This clears the session from AppState but preserves data in database.
        User can resume the session later.

        Returns:
            bool: True if session ended successfully, False if no active session
        """
        if not self.state.current_session_id:
            logger.warning("No active session to end")
            return False

        session_id = self.state.current_session_id
        self.state.current_session_id = None

        logger.info(f"Session {session_id} ended (data preserved in cache)")
        return True

    def get_current_session(self) -> dict | None:
        """Get the current session details from database."""
        if not self.state.current_session_id:
            logger.warning("No active session")
            return None

        with self._get_db() as db:
            session = db.get_session(self.state.current_session_id)

        if not session:
            logger.error(f"Session {self.state.current_session_id} not found in database")
            return None

        logger.info(f"Retrieved session: {session.get('name', 'Unknown')}")
        return session

    def save_current_session(self) -> bool:
        """
        Save current temporary session as permanent.

        Changes is_saved flag from 0 to 1 in database.
        This prevents automatic cleanup of the session.

        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not self.state.current_session_id:
            logger.warning("No active session to save")
            return False

        with self._get_db() as db:
            db.save_session(self.state.current_session_id)

        logger.info(f"Session {self.state.current_session_id} saved as permanent")
        return True

    def resume_session(self, session_id: str) -> bool:
        """
        Resume an existing session and set it as current.

        Security: Verifies that the session belongs to the current user.

        Args:
            session_id: ID of the session to resume

        Returns:
            bool: True if resumed successfully, False otherwise

        Raises:
            AuthenticationError: If user is not authenticated
        """
        if not self.state.is_authenticated:
            raise AuthenticationError("User must be logged in to resume a session")

        with self._get_db() as db:
            session = db.get_session(session_id)

        if not session:
            logger.error(f"Session {session_id} not found")
            return False

        if session.get("user_id") != self.state.current_user_id:
            logger.error(f"Session {session_id} does not belong to current user")
            return False

        self.state.current_session_id = session_id
        logger.info(f"Resumed session: {session.get('name', 'Unknown')}")
        return True

    def list_user_sessions(self) -> list[dict]:
        """
        List all sessions for the current user.

        Returns:
            list[dict]: List of session dicts, empty if not authenticated
        """
        if not self.state.is_authenticated:
            logger.warning("User not authenticated")
            return []

        with self._get_db() as db:
            return db.list_sessions(self.state.current_user_id)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its data.

        Security: Verifies that the session belongs to the current user.
        Side effect: If deleting current session, clears it from AppState.

        Args:
            session_id: ID of the session to delete

        Returns:
            bool: True if deleted successfully, False otherwise

        Raises:
            AuthenticationError: If user is not authenticated
        """
        if not self.state.is_authenticated:
            raise AuthenticationError("User must be logged in to delete a session")

        with self._get_db() as db:
            session = db.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return False

            if session.get("user_id") != self.state.current_user_id:
                logger.error(f"Session {session_id} does not belong to current user")
                return False

            success = db.delete_session(session_id)

        if success:
            if self.state.current_session_id == session_id:
                self.state.current_session_id = None
                logger.info(f"Deleted current session {session_id}")
            else:
                logger.info(f"Deleted session {session_id}")
            return True

        logger.error(f"Failed to delete session {session_id}")
        return False

    def get_verses_by_book(self, book_name: str) -> list[dict]:
        """
        Get all verses for a specific book name.

        Args:
            book_name: Name of the book (e.g., "John", "Genesis")

        Returns:
            List of verse dictionaries
        """
        with self._get_db() as db:
            return db.get_verses_by_book(book_name)

    def get_current_session_verses(self) -> list[dict]:
        """
        Get all verses from the current session.

        Returns:
            List of verse dictionaries, empty list if no active session
        """
        if not self.state.current_session_id:
            logger.warning("No active session")
            return []

        with self._get_db() as db:
            return db.get_all_verses_from_session(self.state.current_session_id)

    def get_verses_from_queries(self, query_ids: list[str]) -> list[dict]:
        """
        Get all verses from multiple query IDs.

        Args:
            query_ids: List of query IDs

        Returns:
            List of verse dictionaries
        """
        with self._get_db() as db:
            return db.get_verses_from_multiple_queries(query_ids)
