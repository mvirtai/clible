import json
import click
from rich.console import Console
from rich.text import Text
from loguru import logger
from typing import TypedDict
from collections import Counter

from app.utils import console
from app.api import fetch_verse_by_reference
from app.utils import render_text_output, render_menu, prompt_menu_choice, MAIN_MENU, ANALYTICS_MENU, highlight_word_in_text, add_vertical_spacing, spacing_before_menu, spacing_after_output, spacing_between_sections
from app.validations.click_params import BookParam, ChapterParam, VersesParam
from app.db.queries import QueryDB


class VerseMatch(TypedDict):
    book: str
    chapter: int
    verse: int
    text: str


def run_main_menu(output: str):
    while True:
        spacing_before_menu()  # Ennen menua
        choice = prompt_menu_choice(MAIN_MENU)

        if choice == 1:
            handle_fetch(
                book=None,
                chapter=None,
                verses=None,
                output=output
            )
            spacing_after_output()  # Yhden rivin väli
        elif choice == 2:
            with QueryDB() as db:
                handle_render_queries(db.show_all_saved_queries())
            spacing_after_output()
        elif choice == 3:
            run_analytic_menu()
            spacing_after_output()
        elif choice == 0:
            console.print("[bold red]Bye[/bold red]")
            break


def render_search_results_info(data: list[VerseMatch], search_word: str) -> None:
    spacing_between_sections()  # 2 riviä ennen uutta osiota
    total_count = len(data)
    book_counts = Counter(row['book'] for row in data)

    if total_count == 1:
        book_name = next(iter(book_counts))
        info_str = f"Found a match for the word {search_word} in the book of {book_name}"
    elif total_count >= 2:
        info_str = f'Found {total_count} matches for the word "{search_word}":'
    
    console.print(info_str)
    spacing_after_output() 
    
    for book, count in book_counts.most_common():
        console.print(f"  • {book}: {count}", markup=False)



def handle_search_word() -> list[VerseMatch]:
    word_input = input("Search word: ").strip()
    if not word_input:
        logger.info("Empty search, try again.")
        return []
    logger.info(f'Searching for "{word_input}"...')

    with QueryDB() as db:
        results = db.search_word(word_input)

    if not results:
        logger.info(f'No matches found for "{word_input}"')
        return results
    
    render_search_results_info(results, word_input)
    input()

    spacing_between_sections()  # 2 riviä ennen tuloksia
    for i, row in enumerate(results):
        ref = f'{row["book"]} {row["chapter"]}:{row["verse"]}'
        highlighted = highlight_word_in_text(row["text"], word_input)
        console.print(f'- [bold]{ref}[/bold]: {highlighted}')

    spacing_after_output()
    return results
    


def run_analytic_menu():
    while True:
        spacing_before_menu()
        choice = prompt_menu_choice(ANALYTICS_MENU)

        if choice == 1:
            results = handle_search_word()
            input("Press any key to continue...")
        elif choice == 0:
            return


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
        spacing_between_sections()  # 2 riviä ennen outputia
        console.print(render_text_output(verse_data))
        spacing_after_output()  # 1 rivi jälkeen

        while True:
            choice = input("Do you want to save the result? [y/N] ").strip().lower()
            if choice in ("y", "n", ""):
                break
            console.print("[red]Please enter y or N.[/red]")
        
        if choice == "y":
            db = QueryDB()
            db.save_query(verse_data)
            

    else:
        logger.error(f"Invalid output choice in flag --output or -o: {output}")



def handle_render_queries(queries: list[dict]) -> None:
    spacing_between_sections()
    if queries:
        console.print("[bold]Saved Queries[/bold]")
        spacing_after_output()
        for q in queries:
            created_at = q["created_at"]
            ref = q["reference"]

            verse_count = q.get("verse_count", 0)
            console.print(
                f"- [bold blue]{ref}[/bold blue] ({verse_count} verses, saved at {created_at})"
            )
    else:
        console.print("[dim]No saved queries found.[/dim]")
    spacing_after_output()
    input("Press any key to continue...")


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
    # result = highlight_word_in_text("tämä on merkkijono", "merkkijono")
    # console.print(result)
