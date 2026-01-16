from pathlib import Path
import click
import json

from app.api import fetch_book_list
from app.export import export_query_to_markdown, EXPORT_DIR
from app.ui import console, spacing_before_menu, spacing_after_output
from app.menus.menu_utils import prompt_menu_choice
from app.menus.menus import MAIN_MENU, ANALYTICS_MENU, EXPORTS_MENU, SESSION_MENU, HISTORY_MENU
from app.validations.click_params import BookParam, ChapterParam, VersesParam
from app.menus.api_menu import run_api_menu
from app.utils import handle_search_word
from app.ui import format_queries
from app.db.queries import QueryDB
from app.analytics.word_frequency import WordFrequencyAnalyzer
from app.analytics.phrase_analysis import PhraseAnalyzer
from app.session_manager import SessionManager
from app.ui import render_book_list

BOOK_LIST_MENU = {
    "title": "=== book list menu ===",
    "options": [
        "Render book list",
        "Fetch book list",
    ],
    "footer": "Exit"
}

def run_book_list_menu():
    while True:
        spacing_before_menu()
        choice = prompt_menu_choice(BOOK_LIST_MENU)

        if choice == 1:
            render_book_list()
            spacing_after_output()
        elif choice == 2:
            fetch_book_list()
            spacing_after_output()
        elif choice == 0:
            return


def select_from_list(items: list[dict], prompt_text: str = "Select item") -> dict | None:
    """
    Display numbered list and let user select by number or ID.
    
    Args:
        items: List of dictionaries with 'id' key
        prompt_text: Text to show in prompt
        
    Returns:
        Selected item dict or None if cancelled/invalid
    """
    if not items:
        return None
    
    # Display numbered list
    for idx, item in enumerate(items, start=1):
        console.print(f"[bold cyan][{idx}][/bold cyan] ", end="")
        
        # Display item info based on type
        if 'name' in item:  # Session item
            status = "💾 Saved" if item.get('is_saved') else "⏱️  Temporary"
            console.print(f"{status} | ID: {item['id']} | Name: {item['name']}", end="")
            if 'scope' in item:
                console.print(f" | Scope: {item['scope']}")
            else:
                console.print()
        elif 'reference' in item:  # Query item
            verse_count = item.get('verse_count', 0)
            console.print(f"ID: {item['id']} | Reference: {item['reference']} | Verses: {verse_count}")
        else:  # Generic item
            console.print(f"ID: {item['id']}")
    
    # Get user input
    user_input = input(f"\n{prompt_text} (number or ID): ").strip()
    
    if not user_input:
        return None
    
    # Try to parse as number first
    try:
        idx = int(user_input)
        if 1 <= idx <= len(items):
            return items[idx - 1]
        else:
            console.print(f"[red]Invalid number. Please select 1-{len(items)}[/red]")
            return None
    except ValueError:
        # Not a number, try to match by ID
        for item in items:
            if item['id'] == user_input:
                return item
        
        console.print("[red]Invalid ID[/red]")
        return None


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
            all_saved_queries = db.show_all_saved_queries()

        if not all_saved_queries:
            console.print("[dim]No saved queries found.[/dim]")
            spacing_before_menu()
        else:
            console.print("\n[bold]Saved queries:[/bold]")

        choice = prompt_menu_choice(EXPORTS_MENU)
        if choice == 1:
            if not all_saved_queries:
                console.print("[yellow]No queries to export.[/yellow]")
                input("Press any key to continue...")
                continue
                
            selected_query = select_from_list(all_saved_queries, "Select query to export")
            
            if selected_query:
                handle_export(selected_query['id'])
            else:
                console.print("[yellow]Export cancelled.[/yellow]")
            
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


def prompt_visualization_choice() -> tuple[bool, str]:
    """
    Prompt user for visualization preferences.
    
    Returns:
        Tuple of (visualize: bool, display_mode: str)
    """
    console.print("\n[bold]Visualization Options:[/bold]")
    console.print("  [1] Show chart in terminal")
    console.print("  [2] Export to file (PNG)")
    console.print("  [3] Both (terminal + export)")
    console.print("  [0] Skip visualization")
    
    viz_choice = input("\nVisualize results? ").strip()
    
    if viz_choice == '1':
        return True, "terminal"
    elif viz_choice == '2':
        return True, "export"
    elif viz_choice == '3':
        return True, "both"
    else:
        return False, "terminal"


def run_analytic_menu():
    while True:
        spacing_before_menu()
        choice = prompt_menu_choice(ANALYTICS_MENU)

        if choice == 1:
            results = handle_search_word()
            input("Press any key to continue...")
        elif choice == 2:
            # Word frequency analysis for single query
            with QueryDB() as db:
                all_saved_queries = db.show_all_saved_queries()
                
                if not all_saved_queries:
                    console.print("[dim]No saved queries found.[/dim]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                console.print("\n[bold]Saved queries:[/bold]")
                selected_query = select_from_list(all_saved_queries, "Select query for word frequency analysis")
                
                if not selected_query:
                    console.print("[yellow]Analysis cancelled.[/yellow]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                # Get verse data
                verse_data = db.get_verses_by_query_id(selected_query['id'])
                
                if verse_data:
                    analyzer = WordFrequencyAnalyzer()
                    
                    # Perform analysis
                    top_words = analyzer.analyze_top(verse_data, top_n=20)
                    vocab_info = analyzer.count_vocabulary_size(verse_data)
                    
                    # Display text results
                    analyzer.show_word_frequency_analysis(verse_data)
                    spacing_after_output()
                    
                    # Prompt for visualization
                    visualize, display_mode = prompt_visualization_choice()
                    if visualize:
                        analyzer.show_word_frequency_analysis(
                            verse_data, 
                            visualize=True, 
                            viz_display=display_mode
                        )
                    
                    # Ask to save to history
                    if input("\nSave this analysis to history? (y/n): ").lower() == 'y':
                        from app.analytics.analysis_tracker import AnalysisTracker
                        from app.state import AppState
                        
                        state = AppState()
                        tracker = AnalysisTracker(
                            user_id=state.current_user_id,
                            session_id=state.current_session_id
                        )
                        tracker.save_word_frequency_analysis(
                            word_freq=top_words,
                            vocab_info=vocab_info,
                            scope_type="query",
                            scope_details={"query_id": selected_query['id']},
                            verse_count=len(verse_data)
                        )
                        console.print("[green]✓ Analysis saved to history![/green]")
                else:
                    console.print("[red]No verses found for the given query.[/red]")
                    spacing_after_output()
                
                input("Press any key to continue...")
        elif choice == 3:
            with QueryDB() as db:
                all_saved_queries = db.show_all_saved_queries()
                
                if not all_saved_queries:
                    console.print("[dim]No saved queries found.[/dim]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                console.print("\n[bold]Saved queries:[/bold]")
                selected_query = select_from_list(all_saved_queries, "Select query for phrase analysis")
                
                if not selected_query:
                    console.print("[yellow]Analysis cancelled.[/yellow]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                verse_data = db.get_verses_by_query_id(selected_query['id'])
                if verse_data:
                    # Perform analysis
                    analyzer = PhraseAnalyzer()
                    analyzer.show_phrase_analysis(verse_data)
                    spacing_after_output()
                    
                    # Prompt for visualization
                    visualize, display_mode = prompt_visualization_choice()
                    if visualize:
                        analyzer.show_phrase_analysis(verse_data, visualize=True, viz_display=display_mode)
                    
                    # Ask to save analysis to history
                    if input("\nSave this analysis to history? (y/n): ").lower() == 'y':
                        from app.analytics.analysis_tracker import AnalysisTracker
                        from app.state import AppState
                        
                        # Get analysis data
                        bigrams = analyzer.analyze_bigrams(verse_data, top_n=20)
                        trigrams = analyzer.analyze_trigrams(verse_data, top_n=20)
                        
                        # Create tracker with current user/session
                        state = AppState()
                        tracker = AnalysisTracker(
                            user_id=state.current_user_id,
                            session_id=state.current_session_id
                        )
                        
                        # Save phrase analysis to database
                        tracker.save_phrase_analysis(
                            bigrams=bigrams,
                            trigrams=trigrams,
                            scope_type="query",
                            scope_details={"query_id": selected_query['id']},
                            verse_count=len(verse_data)
                        )
                        console.print("[green]✓ Phrase analysis saved to history![/green]")
                else:
                    console.print("[red]No verses found for the given query.[/red]")
                    spacing_after_output()
                
                input("Press any key to continue...")
        elif choice == 4:
            # Analyze current session
            session_manager = SessionManager()
            
            if not session_manager.state.has_active_session:
                console.print("[yellow]No active session. Please start or resume a session first.[/yellow]")
                spacing_after_output()
                input("Press any key to continue...")
                continue
            
            console.print(f"\n[bold cyan]Analyzing current session...[/bold cyan]")
            verse_data = session_manager.get_current_session_verses()
            
            if not verse_data:
                console.print("[yellow]No verses found in current session.[/yellow]")
                spacing_after_output()
                input("Press any key to continue...")
                continue
            
            console.print(f"[green]Found {len(verse_data)} verses in session[/green]\n")
            
            # Choose analysis type
            console.print("[bold]Select analysis type:[/bold]")
            console.print("  [1] Word frequency")
            console.print("  [2] Phrase analysis")
            console.print("  [3] Both")
            analysis_choice = input("\nYour choice: ").strip()
            
            if analysis_choice in ['1', '3']:
                console.print("\n[bold cyan]Word Frequency Analysis[/bold cyan]")
                analyzer = WordFrequencyAnalyzer()
                analyzer.show_word_frequency_analysis(verse_data)
                spacing_after_output()
            
            if analysis_choice in ['2', '3']:
                console.print("\n[bold cyan]Phrase Analysis[/bold cyan]")
                analyzer = PhraseAnalyzer()
                analyzer.show_phrase_analysis(verse_data)
                spacing_after_output()
            
            # Visualization prompt
            visualize, display_mode = prompt_visualization_choice()
            if visualize:
                if analysis_choice in ['1', '3']:
                    analyzer = WordFrequencyAnalyzer()
                    analyzer.show_word_frequency_analysis(verse_data, visualize=True, viz_display=display_mode)
                if analysis_choice in ['2', '3']:
                    analyzer = PhraseAnalyzer()
                    analyzer.show_phrase_analysis(verse_data, visualize=True, viz_display=display_mode)
            
            # Ask to save analysis to history
            if input("\nSave this analysis to history? (y/n): ").lower() == 'y':
                from app.analytics.analysis_tracker import AnalysisTracker
                from app.state import AppState
                
                state = AppState()
                tracker = AnalysisTracker(
                    user_id=state.current_user_id,
                    session_id=state.current_session_id
                )
                
                # Save word frequency analysis if performed
                if analysis_choice in ['1', '3']:
                    analyzer = WordFrequencyAnalyzer()
                    top_words = analyzer.analyze_top(verse_data, top_n=20)
                    vocab_info = analyzer.count_vocabulary_size(verse_data)
                    tracker.save_word_frequency_analysis(
                        word_freq=top_words,
                        vocab_info=vocab_info,
                        scope_type="session",
                        scope_details={"session_id": state.current_session_id},
                        verse_count=len(verse_data)
                    )
                
                # Save phrase analysis if performed
                if analysis_choice in ['2', '3']:
                    analyzer = PhraseAnalyzer()
                    bigrams = analyzer.analyze_bigrams(verse_data, top_n=20)
                    trigrams = analyzer.analyze_trigrams(verse_data, top_n=20)
                    tracker.save_phrase_analysis(
                        bigrams=bigrams,
                        trigrams=trigrams,
                        scope_type="session",
                        scope_details={"session_id": state.current_session_id},
                        verse_count=len(verse_data)
                    )
                
                console.print("[green]✓ Analysis saved to history![/green]")
            
            input("Press any key to continue...")
        elif choice == 5:
            # Analyze multiple queries
            with QueryDB() as db:
                all_saved_queries = db.show_all_saved_queries()
                
                if not all_saved_queries:
                    console.print("[dim]No saved queries found.[/dim]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                console.print("\n[bold]Saved queries:[/bold]")
                for idx, query in enumerate(all_saved_queries, start=1):
                    console.print(f"[bold cyan][{idx}][/bold cyan] ID: {query['id']} | {query['reference']} | {query['verse_count']} verses")
                
                console.print("\n[dim]Enter query numbers or IDs separated by commas (e.g., 1,2,5 or abc123,def456)[/dim]")
                user_input = input("\nYour selection: ").strip()
                
                if not user_input:
                    console.print("[yellow]Analysis cancelled.[/yellow]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                # Parse selection
                selected_ids = []
                for item in user_input.split(','):
                    item = item.strip()
                    # Try as number first
                    try:
                        idx = int(item)
                        if 1 <= idx <= len(all_saved_queries):
                            selected_ids.append(all_saved_queries[idx - 1]['id'])
                    except ValueError:
                        # Try as ID
                        if any(q['id'] == item for q in all_saved_queries):
                            selected_ids.append(item)
                
                if not selected_ids:
                    console.print("[red]No valid queries selected.[/red]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                console.print(f"\n[green]Selected {len(selected_ids)} queries[/green]")
                
                # Get combined verses
                verse_data = db.get_verses_from_multiple_queries(selected_ids)
                
                if not verse_data:
                    console.print("[yellow]No verses found in selected queries.[/yellow]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                console.print(f"[green]Found {len(verse_data)} total verses[/green]\n")
                
                # Choose analysis type
                console.print("[bold]Select analysis type:[/bold]")
                console.print("  [1] Word frequency")
                console.print("  [2] Phrase analysis")
                console.print("  [3] Both")
                analysis_choice = input("\nYour choice: ").strip()
                
                if analysis_choice in ['1', '3']:
                    console.print("\n[bold cyan]Word Frequency Analysis[/bold cyan]")
                    analyzer = WordFrequencyAnalyzer()
                    analyzer.show_word_frequency_analysis(verse_data)
                    spacing_after_output()
                
                if analysis_choice in ['2', '3']:
                    console.print("\n[bold cyan]Phrase Analysis[/bold cyan]")
                    analyzer = PhraseAnalyzer()
                    analyzer.show_phrase_analysis(verse_data)
                    spacing_after_output()
                
                # Visualization prompt
                visualize, display_mode = prompt_visualization_choice()
                if visualize:
                    if analysis_choice in ['1', '3']:
                        analyzer = WordFrequencyAnalyzer()
                        analyzer.show_word_frequency_analysis(verse_data, visualize=True, viz_display=display_mode)
                    if analysis_choice in ['2', '3']:
                        analyzer = PhraseAnalyzer()
                        analyzer.show_phrase_analysis(verse_data, visualize=True, viz_display=display_mode)
                
                # Ask to save analysis to history
                if input("\nSave this analysis to history? (y/n): ").lower() == 'y':
                    from app.analytics.analysis_tracker import AnalysisTracker
                    from app.state import AppState
                    
                    state = AppState()
                    tracker = AnalysisTracker(
                        user_id=state.current_user_id,
                        session_id=state.current_session_id
                    )
                    
                    # Save word frequency analysis if performed
                    if analysis_choice in ['1', '3']:
                        analyzer = WordFrequencyAnalyzer()
                        top_words = analyzer.analyze_top(verse_data, top_n=20)
                        vocab_info = analyzer.count_vocabulary_size(verse_data)
                        tracker.save_word_frequency_analysis(
                            word_freq=top_words,
                            vocab_info=vocab_info,
                            scope_type="multi_query",
                            scope_details={"query_ids": selected_ids},
                            verse_count=len(verse_data)
                        )
                    
                    # Save phrase analysis if performed
                    if analysis_choice in ['2', '3']:
                        analyzer = PhraseAnalyzer()
                        bigrams = analyzer.analyze_bigrams(verse_data, top_n=20)
                        trigrams = analyzer.analyze_trigrams(verse_data, top_n=20)
                        tracker.save_phrase_analysis(
                            bigrams=bigrams,
                            trigrams=trigrams,
                            scope_type="multi_query",
                            scope_details={"query_ids": selected_ids},
                            verse_count=len(verse_data)
                        )
                    
                    console.print("[green]✓ Analysis saved to history![/green]")
                
                input("Press any key to continue...")

        elif choice == 6:
            # Analyze by book
            with QueryDB() as db:
                books = db.get_unique_books()
                
                if not books:
                    console.print("[yellow]No books found in database.[/yellow]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                console.print("\n[bold]Available books:[/bold]")
                for idx, book in enumerate(books, start=1):
                    console.print(f"[bold cyan][{idx}][/bold cyan] {book}")
                
                console.print("\n[dim]Enter book number or name[/dim]")
                user_input = input("\nYour selection: ").strip()
                
                if not user_input:
                    console.print("[yellow]Analysis cancelled.[/yellow]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                # Try as number first
                selected_book = None
                try:
                    idx = int(user_input)
                    if 1 <= idx <= len(books):
                        selected_book = books[idx - 1]
                except ValueError:
                    # Try as book name
                    if user_input in books:
                        selected_book = user_input
                
                if not selected_book:
                    console.print("[red]Invalid book selection.[/red]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                console.print(f"\n[bold cyan]Analyzing book: {selected_book}[/bold cyan]")
                
                # Get all verses for the book
                verse_data = db.get_verses_by_book(selected_book)
                
                if not verse_data:
                    console.print(f"[yellow]No verses found for {selected_book}.[/yellow]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue
                
                console.print(f"[green]Found {len(verse_data)} verses[/green]\n")
                
                # Choose analysis type
                console.print("[bold]Select analysis type:[/bold]")
                console.print("  [1] Word frequency")
                console.print("  [2] Phrase analysis")
                console.print("  [3] Both")
                analysis_choice = input("\nYour choice: ").strip()
                
                if analysis_choice in ['1', '3']:
                    console.print("\n[bold cyan]Word Frequency Analysis[/bold cyan]")
                    analyzer = WordFrequencyAnalyzer()
                    analyzer.show_word_frequency_analysis(verse_data)
                    spacing_after_output()
                
                if analysis_choice in ['2', '3']:
                    console.print("\n[bold cyan]Phrase Analysis[/bold cyan]")
                    analyzer = PhraseAnalyzer()
                    analyzer.show_phrase_analysis(verse_data)
                    spacing_after_output()
                
                # Visualization prompt
                visualize, display_mode = prompt_visualization_choice()
                if visualize:
                    if analysis_choice in ['1', '3']:
                        analyzer = WordFrequencyAnalyzer()
                        analyzer.show_word_frequency_analysis(verse_data, visualize=True, viz_display=display_mode)
                    if analysis_choice in ['2', '3']:
                        analyzer = PhraseAnalyzer()
                        analyzer.show_phrase_analysis(verse_data, visualize=True, viz_display=display_mode)
                
                # Ask to save analysis to history
                if input("\nSave this analysis to history? (y/n): ").lower() == 'y':
                    from app.analytics.analysis_tracker import AnalysisTracker
                    from app.state import AppState
                    
                    state = AppState()
                    tracker = AnalysisTracker(
                        user_id=state.current_user_id,
                        session_id=state.current_session_id
                    )
                    
                    # Save word frequency analysis if performed
                    if analysis_choice in ['1', '3']:
                        analyzer = WordFrequencyAnalyzer()
                        top_words = analyzer.analyze_top(verse_data, top_n=20)
                        vocab_info = analyzer.count_vocabulary_size(verse_data)
                        tracker.save_word_frequency_analysis(
                            word_freq=top_words,
                            vocab_info=vocab_info,
                            scope_type="book",
                            scope_details={"book": selected_book},
                            verse_count=len(verse_data)
                        )
                    
                    # Save phrase analysis if performed
                    if analysis_choice in ['2', '3']:
                        analyzer = PhraseAnalyzer()
                        bigrams = analyzer.analyze_bigrams(verse_data, top_n=20)
                        trigrams = analyzer.analyze_trigrams(verse_data, top_n=20)
                        tracker.save_phrase_analysis(
                            bigrams=bigrams,
                            trigrams=trigrams,
                            scope_type="book",
                            scope_details={"book": selected_book},
                            verse_count=len(verse_data)
                        )
                    
                    console.print("[green]✓ Analysis saved to history![/green]")
                
                input("Press any key to continue...")
        elif choice == 7:
            # View analysis history
            run_history_menu()
        elif choice == 0:
            return


def run_history_menu():
    """
    Analysis history menu for viewing and managing saved analyses.
    
    Allows users to:
    - View all saved analyses
    - Filter analyses by type
    - View detailed results of specific analyses
    """
    from app.analytics.analysis_tracker import AnalysisTracker
    from app.state import AppState
    
    state = AppState()
    
    # Check if user is authenticated
    if not state.current_user_id:
        console.print("[yellow]Please log in to view analysis history.[/yellow]")
        input("Press any key to continue...")
        return
    
    tracker = AnalysisTracker(
        user_id=state.current_user_id,
        session_id=state.current_session_id
    )
    
    while True:
        spacing_before_menu()
        choice = prompt_menu_choice(HISTORY_MENU)
        
        if choice == 1:
            # View all analyses
            history = tracker.get_analysis_history(limit=20)
            
            if not history:
                console.print("[yellow]No analysis history found.[/yellow]")
            else:
                console.print(f"\n[bold]Analysis History ({len(history)} records):[/bold]\n")
                console.print(f"{'#':<4} {'Type':<20} {'Scope':<14} {'Verses':<8} {'Created':<20}")
                console.print("─" * 70)
                
                for idx, item in enumerate(history, start=1):
                    console.print(
                        f"{idx:<4} "
                        f"{item['analysis_type']:<20} "
                        f"{item['scope_type']:<14} "
                        f"{item['verse_count']:<8} "
                        f"{item['created_at']:<20}"
                    )
            
            spacing_after_output()
            input("Press any key to continue...")
        elif choice == 2:
            # Filter by analysis type
            console.print("\n[bold]Filter by type:[/bold]")
            console.print("[1] Word frequency")
            console.print("[2] Phrase analysis")
            filter_choice = input("\nYour choice: ").strip()
            
            analysis_type = None
            if filter_choice == '1':
                analysis_type = "word_frequency"
            elif filter_choice == '2':
                analysis_type = "phrase_analysis"
            else:
                console.print("[yellow]Invalid choice.[/yellow]")
                spacing_after_output()
                input("Press any key to continue...")
                continue
            
            history = tracker.get_analysis_history(limit=20, analysis_type=analysis_type)
            
            if not history:
                console.print(f"[yellow]No {analysis_type} analyses found.[/yellow]")
            else:
                console.print(f"\n[bold]{analysis_type.replace('_', ' ').title()} Analyses ({len(history)} records):[/bold]\n")
                console.print(f"{'#':<4} {'Scope':<14} {'Verses':<8} {'Created':<20}")
                console.print("─" * 50)
                
                for idx, item in enumerate(history, start=1):
                    console.print(
                        f"{idx:<4} "
                        f"{item['scope_type']:<14} "
                        f"{item['verse_count']:<8} "
                        f"{item['created_at']:<20}"
                    )
            
            spacing_after_output()
            input("Press any key to continue...")
        elif choice == 3:
            # View specific analysis by ID
            history = tracker.get_analysis_history(limit=10)
            
            if not history:
                console.print("[yellow]No analysis history found.[/yellow]")
                spacing_after_output()
                input("Press any key to continue...")
                continue
            
            console.print("\n[bold]Recent Analyses:[/bold]\n")
            for idx, item in enumerate(history, start=1):
                console.print( 
                    f"[bold cyan][{idx}][/bold cyan] "
                    f"{item['id'][:8]} | "
                    f"{item['analysis_type']:<20} | "
                    f"{item['created_at']}"
                )
            
            user_input = input("\nEnter number or analysis ID: ").strip()
            
            # Try to get analysis ID
            analysis_id = None
            try:
                idx = int(user_input)
                if 1 <= idx <= len(history):
                    analysis_id = history[idx - 1]['id']
            except ValueError:
                analysis_id = user_input
            
            if not analysis_id:
                console.print("[red]Invalid selection.[/red]")
                spacing_after_output()
                input("Press any key to continue...")
                continue
            
            # Get full analysis results
            results = tracker.get_analysis_results(analysis_id)
            
            if not results:
                console.print(f"[red]Analysis {analysis_id} not found.[/red]")
            else:
                # Display analysis details
                console.print(f"\n[bold]═══ Analysis Details ═══[/bold]")
                console.print(f"ID:           {results['id']}")
                console.print(f"Type:         {results['analysis_type']}")
                console.print(f"Scope:        {results['scope_type']}")
                console.print(f"Verses:       {results['verse_count']}")
                console.print(f"Created:      {results['created_at']}")
                console.print(f"\nScope Details: {json.dumps(results['scope_details'], indent=2)}")
                
                # Show results preview
                console.print(f"\n[bold]Results:[/bold]")
                for result_type, data in results['results'].items():
                    console.print(f"\n[cyan]{result_type}:[/cyan]")
                    if isinstance(data, list) and len(data) > 0:
                        # Show top 5 items
                        for item in data[:5]:
                            if isinstance(item, list) and len(item) == 2:
                                console.print(f"  {item[0]:<30} {item[1]:>5}")
                            else:
                                console.print(f"  {item}")
                        if len(data) > 5:
                            console.print(f"  ... and {len(data) - 5} more")
                    elif isinstance(data, dict):
                        for key, value in data.items():
                            console.print(f"  {key}: {value}")
                
                # Show chart paths if available
                if results.get('chart_paths'):
                    console.print(f"\n[bold]Visualizations:[/bold]")
                    for chart_type, path in results['chart_paths'].items():
                        console.print(f"  {chart_type}: {path}")
            
            spacing_after_output()
            input("Press any key to continue...")
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