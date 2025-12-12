class AppState:
    """
    Singleton class that holds application-level state.

    For a CLI application, using a Singleton ensures that all components share
     the same state without needing to pass it around explicitly.

     Attributes:
        current_user_id: ID of the currently logged-in user, or None
        current_session_id: ID of the currently active session, or None
    """

    _instance = None  # Class variable to store the single instance

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
    

if __name__ == "__main__":
        # Step 1:
    state1 = AppState()
    # → __new__(AppState) is called
    # → cls._instance is None, so create it
    # → Initialize it
    # → return cls._instance
    # → state1 now points to that instance

    # Step 2:
    state2 = AppState()
    # → __new__(AppState) is called AGAIN
    # → cls._instance is NOT None anymore!
    # → Skip creation
    # → return cls._instance (same one!)
    # → state2 points to SAME instance as state1

    # Step 3:
    print(state1 is state2)  # True
    # Both variables → same object in memory

    # Step 4:
    state1.current_user_id = "123"
    # Sets attribute on the shared instance

    # Step 5:
    print(state2.current_user_id)  # 123
    # Reading from the same shared instance!