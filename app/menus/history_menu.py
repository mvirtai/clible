import json

from app.ui import console, spacing_before_menu, spacing_after_output
from app.menus.menu_utils import prompt_menu_choice
from app.menus.menus import HISTORY_MENU
from app.analytics.analysis_tracker import AnalysisTracker
from app.state import AppState
from app.db.queries import QueryDB


def run_history_menu():
    """
    Analysis history menu for viewing and managing saved analyses.
    
    Allows users to:
    - View all saved analyses
    - Filter analyses by type
    - View detailed results of specific analyses
    """
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

    # Get current user name
    with QueryDB() as db:
        user = db.get_user_by_id(tracker.user_id)
        user_name = user["name"] if user else "Unknown"

    
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
                console.print(f"{'#':<4} {'User':<15} {'Type':<20} {'Scope':<14} {'Verses':<8} {'Created':<20}")
                console.print("─" * 85)
                
                for idx, item in enumerate(history, start=1):
                    console.print(
                        f"{idx:<4} "
                        f"{item.get('user_name', 'N/A'):<15} "
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

