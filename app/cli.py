import json


def get_ref_values() -> tuple[str, str, str]:
    book = input("Book: ").strip().lower()
    chapter = input("Chapter: ").strip()
    verses = input("Verse(s): ").strip()
    return book, chapter, verses


def display_verse(verse_data: dict) -> None:
    if verse_data:
        print(json.dumps(verse_data, indent=2))
    else:
        print("Failed to fetch verse. Check logs for details.")
