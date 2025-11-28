from loguru import logger
from app.validations.validation_lists import books_list


CHAPTERS_MIN = 1
CHAPTER_MAX = 150
VERSES_MIN = 1
VERSES_MAX = 176


def validate_books(book_ref: str) -> bool:
    if book_ref.strip().lower() in books_list:
        return True
    else:
        return False


def validate_chapter(chapter: str) -> (bool, str):
    if not chapter.isnumeric():
        return (False, "Chapter is not numeric value")
    if int(chapter) not in range(CHAPTERS_MIN, CHAPTER_MAX):
        return (False, f"Chapter is either less than {CHAPTERS_MIN} or more than {CHAPTER_MAX}")
    # palautetaan str-arvona, koska käyttötarkoitus (esim. url-parametri) vaatii str, ei int
    return (True, chapter)


if __name__ == "__main__":
    result = validate_books("JOhn1")
    logger.debug(f"result: {result}")