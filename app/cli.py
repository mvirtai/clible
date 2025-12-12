from pathlib import Path
import click
from loguru import logger

from app.export import export_query_to_markdown, EXPORT_DIR
from app.session_manager import SessionManager
from app.ui import console, spacing_before_menu, spacing_after_output
from app.menus.menu_utils import prompt_menu_choice
from app.menus.menus import MAIN_MENU, ANALYTICS_MENU, EXPORTS_MENU, SESSION_MENU
from app.validations.click_params import BookParam, ChapterParam, VersesParam
from app.menus.api_menu import run_api_menu
from app.utils import handle_search_word
from app.ui import format_queries
from app.db.queries import QueryDB
from app.analytics.word_frequency import WordFrequencyAnalyzer
from app.analytics.phrase_analysis import PhraseAnalyzer


def handle_export(query_id: str):
    if not query_id:
        console.print("[red]✗ No query ID provided[/red]")
        return
    
    output_file = input(f"Output file (press Enter for auto-generated name, will be saved to {EXPORT_DIR}): ").strip()
    output_path = Path(output_file) if output_file else None
        
    result = export_query_to_markdown(query_id, output_path)
        
    if result:
        console.print(f"\n[bold green]✓ Successfully exported to: {result}[/bold green]")
    else:
        console.print(f"\n[red]✗ Failed to export query with ID '{query_id}'[/red]")
    input("Press any key to continue...")


def run_exports_menu():
    while True:
        spacing_after_output()

        # Render all saved queries
        with QueryDB() as db: 
            all_saved_verses = db.show_all_saved_queries()

        if not all_saved_verses:
            console.print("[dim]No saved queries found.[/dim]")
        else:
            console.print("\n[bold]Saved queries:[/bold]")
            for verse in all_saved_verses:
                console.print(f"  ID: {verse['id']} | Reference: {verse['reference']} | Verses: {verse['verse_count']}")
        spacing_before_menu()

        choice = prompt_menu_choice(EXPORTS_MENU)
        if choice == 1:
            query_id = input("\nGive ID: ").strip()
            handle_export(query_id)
            spacing_after_output()
        elif choice == 0:
            return


def run_main_menu(output: str):
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
            run_session_menu()
            spacing_after_output()
        elif choice == 0:
            console.print("[bold red]Bye[/bold red]")
            break


def run_analytic_menu():
    while True:
        spacing_before_menu()
        choice = prompt_menu_choice(ANALYTICS_MENU)

        if choice == 1:
            results = handle_search_word()
            input("Press any key to continue...")
        elif choice == 2:
            with QueryDB() as db:
                all_saved_verses = db.show_all_saved_queries()
                for verse in all_saved_verses:
                    console.print(f"  ID: {verse['id']} | Reference: {verse['reference']} | Verses: {verse['verse_count']}")
                # spacing_before_menu()
                # query_id = input("Give ID: ").strip()
                # verse_data = db.get_verses_by_query_id(query_id)
                # if verse_data:
                #     analyzer = WordFrequencyAnalyzer()
                #     analyzer.show_word_frequency_analysis(verse_data)  
                    spacing_after_output()
                else:
                    console.print("[red]No verses found for the given query ID.[/red]")
                    spacing_after_output()
        elif choice == 3:
            with QueryDB() as db:
                all_saved_verses = db.show_all_saved_queries()
                for verse in all_saved_verses:
                    console.print(f"  ID: {verse['id']} | Reference: {verse['reference']} | Verses: {verse['verse_count']}")
                spacing_before_menu()
                query_id = input("Give ID: ").strip()
                verse_data = db.get_verses_by_query_id(query_id)
                if verse_data:
                    analyzer = PhraseAnalyzer()
                    analyzer.show_phrase_analysis(verse_data)
                else:
                    console.print("[red]No verses found for the given query ID.[/red]")
                    spacing_after_output()
        elif choice == 0:
            return


def run_session_menu():
    session_manager = SessionManager()
    user_name = click.prompt("Give your user name").strip().lower()
    scope = click.prompt("Enter scope (e.g. 'John' or 'Corinthians')").strip()
    console.print()
    console.print(f"[bold cyan]User name:[/bold cyan] {user_name} || [bold green]Scope:[/bold green] {scope}")
    with QueryDB() as db:
        user = db.get_user_by_name(user_name)
        user_id = user["id"] if user else None
        console.print(f"[bold cyan]User ID:[/bold cyan] {user_id} || [bold magenta]User name:[/bold magenta] {user_name} || [bold green]Scope:[/bold green] {scope}")

    current_session = session_manager.get_current_session()
    if current_session:
        console.print(f"[bold cyan]Session ID:[/bold cyan] {current_session['id']} || [bold magenta]Session name:[/bold magenta] {current_session['name']} || [bold green]Scope:[/bold green] {current_session['scope']}")
    else:
        console.print("[yellow]No current session. Available sessions:[/yellow]")
        sessions = session_manager.list_sessions(user_id)
        if sessions:
            for sess in sessions:
                console.print(f"  ID: {sess['id']} | Name: {sess['name']} | Scope: {sess['scope']}")
    while True:
        spacing_before_menu()
        choice = prompt_menu_choice(SESSION_MENU)
        if choice == 1:
            # Start new session
            session_id = session_manager.start_session(user_id, user_name, scope)
            if session_id:
                console.print(f"[bold green]✓ Session created: {session_id}[/bold green]")
            else:
                console.print("[red]✗ Failed to create session[/red]")
            spacing_after_output()
        elif choice == 2:
            # View or set current session
            session = session_manager.get_current_session()
            if session:
                console.print(f"[bold cyan]Session ID:[/bold cyan] {session['id']} || [bold magenta]Session name:[/bold magenta] {session['name']} || [bold green]Scope:[/bold green] {session['scope']}")
            else:
                # Prompt user to select a session
                console.print("[yellow]No current session. Available sessions:[/yellow]")
                sessions = session_manager.list_sessions(user_id)
                if sessions:
                    for sess in sessions:
                        console.print(f"  ID: {sess['id']} | Name: {sess['name']} | Scope: {sess['scope']}")
                    selected_session_id = input("\nEnter session ID to load: ").strip()
                    if selected_session_id:
                        loaded = session_manager.set_current_session(selected_session_id)
                        if loaded:
                            console.print(f"[bold green]✓ Loaded session: {selected_session_id}[/bold green]")
                        else:
                            console.print("[red]✗ Session not found[/red]")
                else:
                    console.print("[dim]No sessions found for this user.[/dim]")
            spacing_after_output()
        elif choice == 3:
            # Delete current session
            if session_manager.delete_session():
                console.print("[bold green]✓ Session deleted successfully.[/bold green]")
            else:
                console.print("[red]✗ No active session to delete[/red]")
            spacing_after_output()
        elif choice == 0:
            return

@click.command()
@click.option('--book', '-b', default=None, type=BookParam(), help='Bible book name (e.g. John)')
@click.option('--chapter', '-c', default=None, type=ChapterParam(), help='Chapter number')
@click.option('--verses', '-v', default=None, type=VersesParam(), help='Verse number(s), e.g. 1 or 1-6')
@click.option('--output', '-o', type=click.Choice(['json', 'text']), default='text', help='Output format')
@click.option('--use-mock/--no-use-mock', '-um/-UM', default=False, show_default=True, help='Load verses from mock_data.json instead of API')
def cli(book, chapter, verses, output, use_mock):
    run_main_menu(output)


if __name__ == "__main__":
    cli()