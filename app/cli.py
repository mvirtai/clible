from pathlib import Path
import click

from app.export import export_query_to_markdown, EXPORT_DIR
from app.utils import console, spacing_before_menu, spacing_after_output
from app.menus.menu_utils import prompt_menu_choice
from app.menus.menus import MAIN_MENU, ANALYTICS_MENU, EXPORTS_MENU
from app.validations.click_params import BookParam, ChapterParam, VersesParam
from app.menus.api_menu import run_api_menu
from app.utils import handle_search_word, format_queries, console
from app.db.queries import QueryDB


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
        db = QueryDB()
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