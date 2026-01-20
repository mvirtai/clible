from app.ui import console, spacing_before_menu, spacing_after_output
from app.menus.menu_utils import prompt_menu_choice, select_from_list
from app.menus.menus import SESSION_MENU
from app.session_manager import SessionManager
from app.db.queries import QueryDB


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
                selected_session = select_from_list(sessions, "Enter session to resume")
                
                if not selected_session:
                    console.print("[yellow]Resume cancelled.[/yellow]")
                elif session_manager.resume_session(selected_session['id']):
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
                selected_session = select_from_list(sessions, "Enter session to delete")
                
                if not selected_session:
                    console.print("[yellow]Deletion cancelled.[/yellow]")
                else:
                    # Show confirmation with session name
                    confirm = input(f"Delete '{selected_session['name']}'? (yes/no): ").strip().lower()
                    
                    if confirm == 'yes':
                        if session_manager.delete_session(selected_session['id']):
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
                selected_session = select_from_list(sessions, "Enter session to clear cache")
                
                if not selected_session:
                    console.print("[yellow]Operation cancelled.[/yellow]")
                else:
                    with QueryDB() as db:
                        if db.clear_session_cache(selected_session['id']):
                            console.print(f"[bold green]✓ Cache cleared for session: {selected_session['name']}[/bold green]")
                        else:
                            console.print("[red]❌ Failed to clear session cache.[/red]")
                            
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
            
            spacing_after_output()
            input("Press any key to continue...")
            
        elif choice == 0:  # Return to main menu
            return

