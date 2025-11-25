import json
import click
from rich.console import Console
from loguru import logger

from app.api import fetch_verse_by_reference
from app.utils import render_text_output


console = Console()

def run_menu(output: str):
    MENU = """
    === clible menu ===
    [1] Fetch verse by reference
    [0] Exit
    """
    while True:
        click.echo(MENU)
        choice = click.prompt("Select option", type=int)

        if choice == 1:
            handle_fetch(
                book=None,
                chapter=None,
                verses=None,
                output=output,
            )
        elif choice == 0:
            click.echo("Bye!")
            break
        else:
            click.echo("Invalid choice, try again.")


def handle_fetch(book: str | None, chapter: str | None, verses: str | None, output: str | None, use_mock: bool = False) -> None:
    book = book or click.prompt("Book").strip().lower()
    chapter = chapter or click.prompt("Chapter").strip()
    verses = verses or click.prompt("Verses").strip()



    verse_data = fetch_verse_by_reference(book, chapter, verses, use_mock)

    if not verse_data:
        click.echo("Failed to fetch verse. Check logs for details.")
        return
    
    if output == "json":
        click.echo(json.dumps(verse_data, indent=2))
    elif output == "text":
        print()
        console.print(render_text_output(verse_data))
        # click.echo(f"{verse_data.get('reference', 'Unknown')}")
        # click.echo(f"{verse_data.get('text').strip()}\n")
    else:
        logger.error(f"Invalid output choice in flag --output or -o: {output}")

@click.command()
@click.option('--book', '-b', default=None, help='Bible book name (e.g. John)')
@click.option('--chapter', '-c', default=None, help='Chapter number')
@click.option('--verses', '-v', default=None, help='Verse number(s), e.g. 1 or 1-6')
@click.option('--output', '-o', type=click.Choice(['json', 'text']), default='text', help='Output format')
@click.option('--use-mock/--no-use-mock', '-um/-NUM', default=False, show_default=True, help='Load verses from mock_data.json instead of API')
def cli(book, chapter, verses, output, use_mock):
    if book and chapter and verses:
        handle_fetch(book, chapter, verses, output, use_mock)
    elif use_mock:
        handle_fetch(book='John', chapter='3', verses='16', output='text', use_mock=True)
    else:
        run_menu(output)


if __name__ == "__main__":
    cli()