import json
import click
from rich.console import Console
from rich.text import Text
from loguru import logger

from app.utils import console
from app.api import fetch_verse_by_reference
from app.utils import render_text_output, render_menu, prompt_menu_choice, MAIN_MENU, ANALYTICS_MENU
from app.validations.click_params import BookParam, ChapterParam, VersesParam
from app.db.queries import QueryDB


def run_analytic_menu():
    while True:
        choice = prompt_menu_choice(ANALYTICS_MENU)

        if choice == 1:
            pass
        elif choice == 2:
            console.print("[bold yellow]Not implemented yet![/bold yellow]")
        elif choice == 0:
            return


def run_main_menu(output: str):
    while True:
        choice = prompt_menu_choice(MAIN_MENU)

        if choice == 1:
            handle_fetch(
                book=None,
                chapter=None,
                verses=None,
                output=output
            )
        elif choice == 2:
            db = QueryDB()
            handle_render_queries(db.show_all_saved_queries())
        elif choice == 3:
            run_analytic_menu()
        elif choice == 0:
            console.print("[bold red]Bye[/bold red]")
            break


def run_menu(output: str):
    

    while True:
        render_menu(MAIN_MENU)
        choice = click.prompt("Select option", type=int)

        if choice == 1:
            handle_fetch(
                book=None,
                chapter=None,
                verses=None,
                output=output,
            )
        elif choice == 2:
            db = QueryDB()
            queries = db.show_all_saved_queries()
            handle_render_queries(queries)
        elif choice == 0:
            click.echo("Bye!")
            break
        else:
            click.echo("Invalid choice, try again.")



def handle_fetch(book: str | None, chapter: str | None, verses: str | None, output: str | None, use_mock: bool = False) -> None:
    book = book or click.prompt("Book", type=BookParam())
    chapter = chapter or click.prompt("Chapter", type=ChapterParam())
    verses = verses or click.prompt("Verses", type=VersesParam())



    verse_data = fetch_verse_by_reference(book, chapter, verses, use_mock)

    if not verse_data:
        click.echo("Failed to fetch verse. Check logs for details.")
        return
    if output == "json":
        click.echo(json.dumps(verse_data, indent=2))
    elif output == "text":
        print()
        console.print(render_text_output(verse_data))
        print()

        while True:
            choice = input("Do you want to save the result? [y/N] ").strip().lower()
            if choice in ("y", "n", ""):
                break
            print("Please enter y or N.")
        
        if choice == "y":
            db = QueryDB()
            db.save_query(verse_data)
            

    else:
        logger.error(f"Invalid output choice in flag --output or -o: {output}")



def handle_render_queries(queries: dict) -> None:
    if queries:
        print("\n[Saved Queries]\n")
        for q in queries:
            created_at = q["created_at"]
            ref = q["reference"]

            verse_count = q.get("verse_count", 0)
            title = Text(ref, style="bold blue")

            console.print(
                f"- [bold blue]{ref}[/bold blue] ({verse_count} verses, saved at {created_at})"
            )
            print("") 
    else:
        print("No saved queries found.\n")


@click.command()
@click.option('--book', '-b', default=None, type=BookParam(), help='Bible book name (e.g. John)')
@click.option('--chapter', '-c', default=None, type=ChapterParam(), help='Chapter number')
@click.option('--verses', '-v', default=None, type=VersesParam(), help='Verse number(s), e.g. 1 or 1-6')
@click.option('--output', '-o', type=click.Choice(['json', 'text']), default='text', help='Output format')
@click.option('--use-mock/--no-use-mock', '-um/-UM', default=False, show_default=True, help='Load verses from mock_data.json instead of API')
def cli(book, chapter, verses, output, use_mock):
    if book and chapter and verses:
        handle_fetch(book, chapter, verses, output, use_mock)
    elif use_mock:
        handle_fetch(book='John', chapter='3', verses='16', output=output, use_mock=True)
    else:
        run_main_menu(output)


if __name__ == "__main__":
    cli()