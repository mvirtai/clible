import json
import requests
import pathlib
from loguru import logger


def get_ref_values() -> tuple[str, str, str]:
    book = input("Book: ").strip().lower()
    chapter = input("Chapter: ").strip()
    verses = input("Verse(s): ").strip()
    return book, chapter, verses


def format_url(book: str, chapter: str, verses: str) -> str:
    return f"https://bible-api.com/{book}+{chapter}:{verses}"


def main():
    ref_values = get_ref_values()
    url = format_url(*ref_values)  # * unpackaa tuplen argumenteiksi
    print(url)

if __name__ == "__main__":
    main()