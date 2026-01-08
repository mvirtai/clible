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
    
    # TODO: Implement methods
    # We'll do these one by one!

    def start_session(self, name: str, scope: str, temporary: bool = False) -> str | None:
        """Create a new temporary session and set it as current session."""
        if not self.state.is_authenticated:
            raise AuthenticationError("User must be logged in to start a session.")
 
        with QueryDB(self.db_path) as db:
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
        self.state.current_session_id = None  # Clear from AppState
        
        logger.info(f"Session {session_id} ended (data preserved in cache)")
        return True
    

    def get_current_session(self) -> dict | None:
        """Get the current session details from database."""
        if not self.state.current_session_id:
            logger.warning("No active session")
            return None
        
        with QueryDB(self.db_path) as db:
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
        
        with QueryDB(self.db_path) as db:
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
        
        with QueryDB(self.db_path) as db:
            session = db.get_session(session_id)
        
        if not session:
            logger.error(f"Session {session_id} not found")
            return False
        
        # Security check: verify session belongs to current user
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
        
        with QueryDB(self.db_path) as db:
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
        
        with QueryDB(self.db_path) as db:
            # Security check: verify session belongs to current user
            session = db.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return False
            
            if session.get("user_id") != self.state.current_user_id:
                logger.error(f"Session {session_id} does not belong to current user")
                return False
            
            # Delete the session
            success = db.delete_session(session_id)
        
        if success:
            # If we deleted the current session, clear it from AppState
            if self.state.current_session_id == session_id:
                self.state.current_session_id = None
                logger.info(f"Deleted current session {session_id}")
            else:
                logger.info(f"Deleted session {session_id}")
            return True
        
        logger.error(f"Failed to delete session {session_id}")
        return False



if __name__ == "__main__":
    # Test the session manager

    # Step 1: Create a new user directly in the database
    with QueryDB() as db_test:
        user_id = db_test.create_user("test_user")
        logger.info(f"User created with ID: {user_id}")

    # Step 2: Set user in AppState (to simulate login)
    session_manager = SessionManager()
    session_manager.state.current_user_id = user_id

    # Step 3: Start a temporary session
    session_id = session_manager.start_session(
        name="Test Session",
        scope="Revelation chapters 1-3",
        temporary=True,
    )
    logger.info(f"Session started with ID: {session_id}")

    # Step 4: Get current session details
    # session_details = session_manager.get_current_session()
    # print(f"Session data: {session_details}")

    session_manager.end_session()
