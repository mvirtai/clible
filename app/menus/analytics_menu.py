from app.ui import console, spacing_before_menu, spacing_after_output
from app.menus.menu_utils import prompt_menu_choice, select_from_list, parse_selection_range
from app.menus.menus import ANALYTICS_MENU
from app.menus.history_menu import run_history_menu
from app.utils import handle_search_word
from app.db.queries import QueryDB
from app.analytics.word_frequency import WordFrequencyAnalyzer
from app.analytics.phrase_analysis import PhraseAnalyzer
from app.analytics.analysis_tracker import AnalysisTracker
from app.state import AppState
from app.session_manager import SessionManager


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
    """Handle the Analytics submenu."""
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

                selected_ids = parse_selection_range(user_input, len(all_saved_queries))

                if not selected_ids:
                    console.print("[yellow]Analysis cancelled.[/yellow]")
                    spacing_after_output()
                    input("Press any key to continue...")
                    continue

                # Convert indices to query_ids
                query_ids = [all_saved_queries[idx - 1]['id'] for idx in selected_ids]

                console.print(f"\n[green]Selected {len(query_ids)} queries[/green]")
                for idx, query_id in enumerate(query_ids, start=1):
                    query = next(q for q in all_saved_queries if q['id'] == query_id)
                    console.print(f"[bold cyan][{idx}][/bold cyan] ID: {query_id} | {query['reference']} | {query['verse_count']} verses")
                input("Press any key to continue...")

                # Get combined verses
                verse_data = db.get_verses_from_multiple_queries(query_ids)
                
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
