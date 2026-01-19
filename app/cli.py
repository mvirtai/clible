import click

from app.ui import console, spacing_before_menu, spacing_after_output
from app.menus.menu_utils import prompt_menu_choice
from app.menus.menus import MAIN_MENU
from app.validations.click_params import BookParam, ChapterParam, VersesParam
from app.menus.api_menu import run_api_menu
from app.menus.analytics_menu import run_analytic_menu
from app.menus.exports_menu import run_exports_menu
from app.menus.session_menu import run_session_menu
from app.ui import format_queries
from app.db.queries import QueryDB
from app.session_manager import SessionManager


def run_main_menu(output: str, username: str):
    """
    Main menu loop with integrated session management.
    
    Args:
        output: Output format for display
        username: Username for authentication
    """
    # Initialize SessionManager
    session_manager = SessionManager()
    
    # Auto-login: get or create user and authenticate
    with QueryDB() as db:
        user_id = db.get_or_create_default_user(username)
    
    if not user_id:
        console.print("[red]❌ Failed to authenticate user.[/red]")
        return
    
    # Set authenticated user in AppState
    session_manager.state.current_user_id = user_id
    
    # Show login status
    console.print(f"[dim]👤 Logged in as: [bold]{username}[/bold][/dim]\n")

    while True:
        spacing_before_menu()
        choice = prompt_menu_choice(MAIN_MENU)
        if choice == 1:
            run_api_menu(output)
            spacing_after_output()
        elif choice == 2:
            with QueryDB() as db:
                queries = db.show_all_saved_queries()
                for query in format_queries(queries):
                    console.print(query)
            spacing_after_output()
            input("Press any key to continue...")
        elif choice == 3:
            run_analytic_menu()
            spacing_after_output()
        elif choice == 4:
            run_exports_menu()
            spacing_after_output()
        elif choice == 5:
            run_session_menu(session_manager)
            spacing_after_output()
        elif choice == 0:
            console.print("[bold red]Bye[/bold red]")
            break


@click.command()
@click.option('--user', '-u', default='default', help='Username for session (default: "default")')
@click.option('--book', '-b', default=None, type=BookParam(), help='Bible book name (e.g. John)')
@click.option('--chapter', '-c', default=None, type=ChapterParam(), help='Chapter number')
@click.option('--verses', '-v', default=None, type=VersesParam(), help='Verse number(s), e.g. 1 or 1-6')
@click.option('--output', '-o', type=click.Choice(['json', 'text']), default='text', help='Output format')
@click.option('--use-mock/--no-use-mock', '-um/-UM', default=False, show_default=True, help='Load verses from mock_data.json instead of API')
def cli(user, book, chapter, verses, output, use_mock):
    run_main_menu(output, username=user)


if __name__ == "__main__":
    cli()
