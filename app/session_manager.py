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
    
def end_session(self) -> bool:
    """End current session, keeping data in cache."""
    if not self.state.current_session_id:
        logger.warning("No active session to end")
        return False
    
    session_id = self.state.current_session_id
    self.state.current_session_id = None  # Clear from AppState
    
    logger.info(f"Session {session_id} ended (data preserved in cache)")
    return True

    
    def save_current_session(self) -> bool:
        """Save current session into database."""
        session_id = self.state.current_session_id
        if not session_id:
            logger.warning("No active session to end.")
            return False
        
        with QueryDB() as db:
            db.save_session(session_id)
            logger.info(f"Session {session_id}")
            return True


    def save_current_session(self) -> bool:
        if not self.state.current_session_id:
            logger.warning("No active session to save.")
            return False
        with QueryDB() as db:
            db.save_session(self.state.current_session_id)
            logger.info(f"Session {self.state.current_session_id} saved.")
            return True

    
    def list_user_sessions(self) -> list[dict]:
        if not self.state.is_authenticated:
            raise AuthenticationError("User must be logged in to list sessions.")
        
        with QueryDB() as db:
            sessions = db.list_sessions(self.state.current_user_id)
            return sessions


    def resume_session(self, session_id: str) -> False:
        if not self.state.is_authenticated:
            raise AuthenticationError
        
        with QueryDB() as db:
            session = db.get_session(session_id)
        
        if session["id"] != session_id:
            logger.error(f"Session {session_id} not found in database")
            return False
        
        self.state.current_session_id = session_id
        logger.info(f"Session {session_id} resumed.")
        return True

    def delete_session(self, session_id: str) -> bool:
        if not self.state.is_authenticated:
            raise AuthenticationError("User must be logged in to delete a session.")
        
            with QueryDB() as db:
                return db.delete_session(session_id)
                logger.info(f"Session {session_id} deleted.")
                return True
        else:
            logger.error(f"Failed to delete session {session_id}")
            return False
        return False

    def clear_session_cache(self, session_id: str) -> bool:
        if not self.state.is_authenticated:
            raise AuthenticationError("User must be logged in to clear session cache.")
            
            with QueryDB() as db:
                return db.clear_session_cache(session_id)
                logger.info(f"Session {session_id} cache cleared.")
                return True
        else:
            logger.error(f"Failed to clear session cache {session_id}")
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

    # Step 4: Save the session
    session_manager.save_current_session()
    logger.info(f"Session {session_id} saved.")