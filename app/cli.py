import json
import click
from rich.console import Console
from rich.text import Text
from loguru import logger
from typing import TypedDict
from collections import Counter

from app.utils import console
from app.api import fetch_by_reference
from app.utils import render_text_output, highlight_word_in_text, add_vertical_spacing, spacing_before_menu, spacing_after_output, spacing_between_sections
from app.menus.menu_utils import render_menu, prompt_menu_choice
from app.menus.menus import MAIN_MENU, ANALYTICS_MENU
from app.validations.click_params import BookParam, ChapterParam, VersesParam
from app.db.queries import QueryDB
from app.menus.api_menu import run_api_menu


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
            run_api_menu(output)
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
        info_str = f"Found a match for the word '{search_word}' in the book of {book_name}"
    elif total_count >= 2:
        info_str = f'Found {total_count} matches for the word "{search_word}":'
    else:
        info_str = f'No matches found for the word "{search_word}"'
    
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
    run_main_menu(output)


if __name__ == "__main__":
    cli()
    # result = highlight_word_in_text("tämä on merkkijono", "merkkijono")
    # console.print(result)
