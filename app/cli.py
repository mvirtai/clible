from pathlib import Path
import click

from app.export import export_query_to_markdown, EXPORT_DIR
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
from app.session_manager import SessionManager
from app.session_manager import SessionManager

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


    # while True:
    #     spacing_before_menu()
    #     choice = prompt_menu_choice(MAIN_MENU)

    #     if choice == 1:
    #         run_api_menu(output)
    #         spacing_after_output()
    #     elif choice == 2:
    #         with QueryDB() as db:
    #             queries = db.show_all_saved_queries()
    #             for query in format_queries(queries):
    #                 console.print(query)
    #         spacing_after_output()
    #         input("Press any key to continue...")
    #     elif choice == 3:
    #         run_analytic_menu()
    #         spacing_after_output()
    #     elif choice == 4:
    #         run_exports_menu()
    #         spacing_after_output()
    #     elif choice == 5:
    #         run_session_menu()
    #         spacing_after_output()
    #     elif choice == 0:
    #         console.print("[bold red]Bye[/bold red]")
    #         break


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
                spacing_before_menu()
                query_id = input("Give ID: ").strip()
                verse_data = db.get_verses_by_query_id(query_id)
                if verse_data:
                    analyzer = WordFrequencyAnalyzer()
                    analyzer.show_word_frequency_analysis(verse_data)  
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


def run_session_menu(session_manager: SessionManager):
    """
    Session management menu using SessionManager for coordinated operations.
    
    Args:
        session_manager: SessionManager instance with authenticated user
    """
    while True:
        spacing_before_menu()
        
        # Show current session status
        if session_manager.state.has_active_session:
            current = session_manager.get_current_session()
            if current:
                console.print(f"[dim]📂 Active session: [bold]{current['name']}[/bold] (ID: {current['id']})[/dim]")
        
        choice = prompt_menu_choice(SESSION_MENU)
        
        if choice == 1:  # Start new session
            try:
                session_name = input("Enter session name: ").strip()
                if not session_name:
                    console.print("[yellow]Session name cannot be empty.[/yellow]")
                    continue
                    
                scope = input("Enter scope (e.g. John 1-3, Paul's letters): ").strip()
                temporary = input("Temporary session? (y/n, default: y): ").strip().lower() != 'n'
                
                session_id = session_manager.start_session(session_name, scope, temporary=temporary)
                
                if session_id:
                    console.print(f"[bold green]✓ Session started: {session_name}[/bold green]")
                    console.print(f"[dim]Session ID: {session_id}[/dim]")
                else:
                    console.print("[red]❌ Failed to start session.[/red]")
                    
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
            
            spacing_after_output()
            input("Press any key to continue...")
        elif choice == 2:  # Resume session
            try:
                # List available sessions first
                sessions = session_manager.list_user_sessions()
                
                if not sessions:
                    console.print("[dim]No sessions available to resume.[/dim]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                console.print("\n[bold]Your sessions:[/bold]")
                for session in sessions:
                    status = "💾 Saved" if session.get('is_saved') else "⏱️  Temporary"
                    console.print(f"  {status} | ID: {session['id']} | Name: {session['name']} | Scope: {session['scope']}")
                
                session_id = input("\nEnter session ID to resume: ").strip()
                
                if session_manager.resume_session(session_id):
                    resumed = session_manager.get_current_session()
                    console.print(f"[bold green]✓ Resumed session: {resumed['name']}[/bold green]")
                else:
                    console.print("[red]❌ Failed to resume session.[/red]")
                    
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
            
            spacing_after_output()
            input("Press any key to continue...")
            
        elif choice == 3:  # End current session
            if not session_manager.state.has_active_session:
                console.print("[yellow]No active session to end.[/yellow]")
            else:
                current = session_manager.get_current_session()
                if session_manager.end_session():
                    console.print(f"[bold green]✓ Session ended: {current['name']}[/bold green]")
                    console.print("[dim]Session data is preserved and can be resumed later.[/dim]")
                else:
                    console.print("[red]❌ Failed to end session.[/red]")
            
            spacing_after_output()
            input("Press any key to continue...")
            
        elif choice == 4:  # Save current session
            if not session_manager.state.has_active_session:
                console.print("[yellow]No active session to save.[/yellow]")
            else:
                current = session_manager.get_current_session()
                if current.get('is_saved'):
                    console.print("[yellow]Session is already saved as permanent.[/yellow]")
                else:
                    if session_manager.save_current_session():
                        console.print(f"[bold green]✓ Session saved as permanent: {current['name']}[/bold green]")
                        console.print("[dim]This session will not be automatically deleted.[/dim]")
                    else:
                        console.print("[red]❌ Failed to save session.[/red]")
            
            spacing_after_output()
            input("Press any key to continue...")
            
        elif choice == 5:  # List sessions
            sessions = session_manager.list_user_sessions()
            
            if not sessions:
                console.print("[dim]No sessions found.[/dim]")
            else:
                console.print("\n[bold]Your sessions:[/bold]")
                for session in sessions:
                    # Show if it's the active session
                    active_marker = "🔵 " if session['id'] == session_manager.state.current_session_id else "   "
                    status = "💾 Saved" if session.get('is_saved') else "⏱️  Temporary"
                    console.print(f"{active_marker}{status} | ID: {session['id']} | Name: {session['name']} | Scope: {session['scope']}")
            
            spacing_after_output()
            input("Press any key to continue...")
            
        elif choice == 6:  # Delete session
            try:
                # List available sessions first
                sessions = session_manager.list_user_sessions()
                
                if not sessions:
                    console.print("[dim]No sessions available to delete.[/dim]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                console.print("\n[bold]Your sessions:[/bold]")
                for session in sessions:
                    status = "💾 Saved" if session.get('is_saved') else "⏱️  Temporary"
                    console.print(f"  {status} | ID: {session['id']} | Name: {session['name']}")
                
                session_id = input("\nEnter session ID to delete: ").strip()
                confirm = input(f"Are you sure you want to delete this session? (yes/no): ").strip().lower()
                
                if confirm == 'yes':
                    if session_manager.delete_session(session_id):
                        console.print("[bold green]✓ Session deleted successfully.[/bold green]")
                    else:
                        console.print("[red]❌ Failed to delete session.[/red]")
                else:
                    console.print("[yellow]Deletion cancelled.[/yellow]")
                    
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
            
            spacing_after_output()
            input("Press any key to continue...")
            
        elif choice == 7:  # Clear session cache
            try:
                # List available sessions first
                sessions = session_manager.list_user_sessions()
                
                if not sessions:
                    console.print("[dim]No sessions available.[/dim]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                console.print("\n[bold]Your sessions:[/bold]")
                for session in sessions:
                    console.print(f"  ID: {session['id']} | Name: {session['name']}")
                
                session_id = input("\nEnter session ID to clear cache: ").strip()
                
                # Verify ownership before clearing cache
                session = None
                for s in sessions:
                    if s['id'] == session_id:
                        session = s
                        break
                
                if not session:
                    console.print("[red]❌ Session not found or doesn't belong to you.[/red]")
                else:
                    with QueryDB() as db:
                        if db.clear_session_cache(session_id):
                            console.print("[bold green]✓ Session cache cleared successfully.[/bold green]")
                        else:
                            console.print("[red]❌ Failed to clear session cache.[/red]")
                            
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
            
            spacing_after_output()
            input("Press any key to continue...")
            
        elif choice == 0:  # Return to main menu
            return

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