
from app.db.queries import QueryDB

class SessionManager:
    """Manages current session state in memory."""
    
    def __init__(self):
        self.current_session = None
        self.current_user = None
        self.current_scope = None
    
    def start_session(self, user_id: str, name: str, scope: str) -> str | None:
        """Start a new session and set it as current."""
        if user_id:
            with QueryDB() as db:
                session_id = db.create_session(user_id, name, scope, is_saved=False)
                if session_id:
                    # Get the full session object
                    self.current_session = db.get_session(session_id)
                    return session_id
        return None
         
    def get_current_session(self) -> dict | None:
        """Get the current session."""
        return self.current_session
    
    def set_current_session(self, session_id: str) -> dict | None:
        """Set an existing session as current by its ID."""
        if session_id:
            with QueryDB() as db:
                self.current_session = db.get_session(session_id)
                return self.current_session
        return None
    
    def list_sessions(self, user_id: str | None = None) -> list[dict]:
        """List all sessions for a user. Returns empty list if user_id is None."""
        if user_id:
            with QueryDB() as db:
                return db.list_sessions(user_id)
        return []
    
    def add_query_to_session(self, query_id: str) -> dict | None:
        """Add a query to the current session."""
        if self.current_session and query_id:
            session_id = self.current_session.get('id')
            if session_id:
                with QueryDB() as db:
                    db.add_query_to_session(session_id, query_id)
                    return self.current_session
        return None

    def save_session(self) -> dict | None:
        """Save the current session (mark as permanent)."""
        if self.current_session:
            session_id = self.current_session.get('id')
            if session_id:
                with QueryDB() as db:
                    db.save_session(session_id)
                    return self.current_session
        return None
    
    def delete_session(self) -> bool:
        """Delete the current session."""
        if self.current_session:
            session_id = self.current_session.get('id')
            if session_id:
                with QueryDB() as db:
                    result = db.delete_session(session_id)
                    if result:
                        self.current_session = None  # Clear current session
                    return result
        return False
    
    def get_session_queries(self) -> list[dict]:
        """Get all queries for the current session."""
        if self.current_session:
            session_id = self.current_session.get('id')
            if session_id:
                with QueryDB() as db:
                    return db.get_session_queries(session_id)
        return []
    
    def clear_session_cache(self) -> bool:
        """Clear the cache for the current session."""
        if self.current_session:
            session_id = self.current_session.get('id')
            if session_id:
                with QueryDB() as db:
                    return db.clear_session_cache(session_id)
        return False
