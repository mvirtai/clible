
from app.db.queries import QueryDB

class SessionManager:
    def __init__(self, db: QueryDB):
        self.db = QueryDB()
        self.current_session = None
        self.current_user = None
    

    def start_session(self, user_id: str, name: str, scope: str) -> str | None:
        if user_id:
            with self.db as db:
                self.current_session = db.create_session(user_id, name, scope, is_saved=False)
                if self.current_session:
                    return self.current_session
                return None
        return None

    def get_current_session(self) -> dict | None:
        return self.current_session
    
    def set_current_session(self, session_id: str) -> None:
        if session_id:
            with self.db as db:
                self.current_session = db.get_session(session_id)
                if self.current_session:
                    return self.current_session
                return None
        return None
    
    def list_sessions(self, user_id: str | None = None) -> list[dict]:
        if user_id:
            with self.db as db:
                return db.list_sessions(user_id)
        return []
    
    def add_query_to_session(self, query_id: str) -> None:
        if self.current_session and query_id:
            with self.db as db:
                db.add_query_to_session(self.current_session, query_id)
                return self.current_session
        return None

    def save_session(self) -> None:
        if self.current_session:
            with self.db as db:
                db.save_session(self.current_session)
                return self.current_session
        return None
    
    def delete_session(self) -> bool:
        if self.current_session:
            with self.db as db:
                return db.delete_session(self.current_session)
        return False
    
    def get_session_queries(self) -> list[dict]:
        if self.current_session:
            with self.db as db:
                return db.get_session_queries(self.current_session)
        return []
    
    def clear_session_cache(self) -> bool:
        if self.current_session:
            with self.db as db:
                return db.clear_session_cache(self.current_session)
        return False