from pathlib import Path

from app.ui import console, spacing_before_menu, spacing_after_output
from app.menus.menu_utils import prompt_menu_choice, select_from_list
from app.menus.menus import EXPORTS_MENU
from app.export import export_query_to_markdown, EXPORT_DIR
from app.db.queries import QueryDB


def handle_export(query_id: str):
    """Handle exporting a query to markdown."""
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
    """Handle the Exports submenu."""
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

