# app/menus/api_menu.py
import click
from loguru import logger

from app.utils import (
    console, render_text_output, spacing_before_menu, spacing_after_output,
    spacing_between_sections,
)
from app.menus.menu_utils import prompt_menu_choice
from app.menus.menus import MAIN_MENU, API_MENU, ANALYTICS_MENU
from app.validations.click_params import BookParam, ChapterParam, VersesParam
from app.api import fetch_by_reference
from app.db.queries import QueryDB


def run_api_menu(output: str):
    """Handle the Fetch from API submenu."""
    while True:
        spacing_before_menu()
        choice = prompt_menu_choice(API_MENU)

        if choice == 1:
            verse_data = handle_fetch_by_ref('v')
            if verse_data:
                spacing_between_sections()
                console.print(render_text_output(verse_data))
                handle_save(verse_data)
        elif choice == 2:
            chapter_data = handle_fetch_by_ref('c')
            if chapter_data:
                spacing_between_sections()
                console.print(render_text_output(chapter_data))
                handle_save(chapter_data)
            spacing_after_output()
        elif choice == 3:
            random_verse_data = handle_fetch_by_ref('r')
            if random_verse_data:
                spacing_between_sections()
                console.print(render_text_output(random_verse_data))
            spacing_after_output()
        elif choice == 0:
            return



def handle_fetch_by_ref(mode: str) -> dict | None:
    if mode == 'v':
        # Fetch verse by reference
        book = click.prompt("Book", type=BookParam())
        chapter = click.prompt("Chapter", type=ChapterParam())
        verses = click.prompt("Verses", type=VersesParam())

        data = fetch_by_reference(book, chapter, verses)
        word = 'verse(s)'
    elif mode == 'c':
        # Fetch chapter by reference
        book = click.prompt("Book", type=BookParam())
        chapter = click.prompt("Chapter", type=ChapterParam())

        data = fetch_by_reference(book, chapter, None)
        word = 'chapter'
    elif mode == 'r':
        # Fetch random verse
        data = fetch_by_reference(None, None, None, True)
        word = 'random verse'
    else:
        logger.error(f"Invalid mode: {mode}. Must be 'v', 'c', or 'r'")
        return None

    if not data:
        logger.error("Failed to fetch verse. Check logs for details.")
        return None
    
    logger.info(f"Fetched {word} successfully")
    return data


def handle_save(data: dict):
    choice = click.confirm("Do you want to save result the result? [y/N] ", default=True)

    if choice:
        try:
            with QueryDB() as db:
                db.save_query(data)
            logger.info("Result saved successfully")
        except Exception as e:
            logger.error(f"Failed to save result: {e}")
    else:
        logger.info("Result not saved")
