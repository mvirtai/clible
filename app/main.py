from loguru import logger
from app.cli import get_ref_values, display_verse
from app.utils import format_ref, format_url
from app.api import fetch_verse_by_reference


def main():
    ref_tuple = get_ref_values()
    verse_data = fetch_verse_by_reference(*ref_tuple)
    display_verse(verse_data)

    

if __name__ == "__main__":
    main()