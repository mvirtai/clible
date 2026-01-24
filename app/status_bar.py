"""
Status bar component for clible.

Displays current user and active session in the terminal.
"""

from app.db.queries import QueryDB
from app.state import AppState
from app.ui import console
from rich.panel import Panel
from rich.align import Align


class StatusBar:
    """Status bar that displays the current session and user information."""
    def __init__(self):
        self.current_session = None
        self.current_user = None

    def update(self):
        """Update the status bar with the current session and user information."""
        state = AppState()

        # Resolve current user
        self.current_user = None
        if state.current_user_id:
            with QueryDB() as db:
                self.current_user = db.get_user_by_id(state.current_user_id)

        # Resolve current session
        self.current_session = None
        if state.current_session_id:
            with QueryDB() as db:
                self.current_session = db.get_session(state.current_session_id)

    def display(self):
        """Display the status bar."""
        state = AppState()
        user_label = (
            self.current_user["name"]
            if isinstance(self.current_user, dict) and self.current_user.get("name")
            else "None"
        )
        session_label = (
            self.current_session.get("name")
            if isinstance(self.current_session, dict)
            else None
        )
        session_label = session_label or "None"

        user_id = state.current_user_id
        session_id = (
            self.current_session.get("id")
            if isinstance(self.current_session, dict)
            else None
        )
        is_saved = (
            self.current_session.get("is_saved")
            if isinstance(self.current_session, dict)
            else None
        )
        scope = (
            self.current_session.get("scope")
            if isinstance(self.current_session, dict)
            else None
        )

        session_meta = []
        if session_id:
            session_meta.append(f"id: {session_id}")
        if is_saved is not None:
            session_meta.append("saved" if is_saved else "temp")
        if scope:
            session_meta.append(f"scope: {scope}")

        session_meta_str = " | ".join(session_meta) if session_meta else "no session"
        user_meta_str = f"id: {user_id}" if user_id else "not authenticated"

        bar_text = "\n".join(
            [
                f"[bold cyan]User[/bold cyan]: [white]{user_label}[/white] ([dim]{user_meta_str}[/dim])",
                f"[bold magenta]Session[/bold magenta]: [white]{session_label}[/white] ([dim]{session_meta_str}[/dim])",
            ]
        )

        panel = Panel(
            Align.left(bar_text),
            title="[green]Status[/green]",
            border_style="dim",
            padding=(0, 0),
            expand=False,
        )
        console.print(panel)

    def run(self):
        """Update and display the status bar once."""
        self.update()
        self.display()