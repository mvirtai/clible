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
    
    def __init__(self):
        """Initialize SessionManager with reference to AppState singleton."""
        self.state = AppState()
    
    # TODO: Implement methods
    # We'll do these one by one!

    def start_session(self, name: str, scope: str, temporary: bool = False) -> str | None:
        """Create a new temporary session and set it as current session."""
        if not self.state.is_authenticated:
            raise AuthenticationError("User must be logged in to start a session.")
 
        with QueryDB() as db:
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
    

    def get_current_session(self) -> dict | None:
        """Get the current session details from database."""
        if not self.state.current_session_id:
            logger.warning("No active session")
            return None
        
        with QueryDB() as db:
            session = db.get_session(self.state.current_session_id)
        
        if not session:
            logger.error(f"Session {self.state.current_session_id} not found in database")
            return None
            
        logger.info(f"Retrieved session: {session.get('name', 'Unknown')}")
        return session



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
    session_details = session_manager.get_current_session()
    print(f"Session data: {session_details}")