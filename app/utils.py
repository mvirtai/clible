"""
Utility functions for business logic and workflow orchestration.

This module contains functions that combine business logic (database operations,
input handling) with UI rendering. Pure rendering functions are in ui.py.
"""

from loguru import logger

from app.db.queries import QueryDB
from app.ui import (
    console,
    render_search_results_info,
    highlight_word_in_text,
    spacing_between_sections,
    spacing_after_output,
    VerseMatch,
)


def handle_search_word() -> list[VerseMatch]:
    """
    Handle the word search workflow: prompt user, query database, and render results.

    Returns:
        List of verse match dictionaries
    """
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

    spacing_between_sections()
    for i, row in enumerate(results):
        ref = f'{row["book"]} {row["chapter"]}:{row["verse"]}'
        highlighted = highlight_word_in_text(row["text"], word_input)
        console.print(f'- [bold]{ref}[/bold]: {highlighted}')

    spacing_after_output()
    return results
