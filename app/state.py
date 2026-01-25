"""
Application-level state singleton for clible.

Holds current_user_id and current_session_id shared across menus and components.
"""


class AppState:
    """
    Singleton class that holds application-level state.

    For a CLI application, using a Singleton ensures that all components share
    the same state without needing to pass it around explicitly.

    Attributes:
        current_user_id: ID of the currently logged-in user, or None
        current_session_id: ID of the currently active session, or None
    """

    _instance = None

    def __new__(cls):
        """
        Override __new__ to implement Singleton pattern.

        This ensures only one instance of AppState ever exists.
        Every call to AppState() returns the same instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the state variables. Called only once."""
        self.current_user_id: str | None = None
        self.current_session_id: str | None = None

    @property
    def is_authenticated(self) -> bool:
        """Returns True if the user is authenticated, False otherwise."""
        return bool(self.current_user_id)

    @property
    def has_active_session(self) -> bool:
        """Returns True if the user has an active session, False otherwise."""
        return bool(self.current_session_id)

    def clear(self) -> None:
        """Reset state. Useful for testing and logging out."""
        self.current_user_id = None
        self.current_session_id = None
