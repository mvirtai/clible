from loguru import logger
from app.validations.validation_lists import books_list


CHAPTERS_MIN = 1
CHAPTER_MAX = 150
VERSES_MIN = 1
VERSES_MAX = 175


def validate_books(book_ref: str) -> bool:
    if book_ref.strip().lower() in books_list:
        return True
    else:
        return False


def validate_chapter(chapter: str) -> (bool, str):
    chapter = chapter.strip()
    if not chapter.isnumeric():
        try:
            num = int(chapter)
            if num < CHAPTERS_MIN or num > CHAPTER_MAX:
                return (False, f"Chapter is either less than {CHAPTERS_MIN} or more than {CHAPTER_MAX}")
        except ValueError:
            pass
        return (False, "Chapter is not numeric value")
    if int(chapter) not in range(CHAPTERS_MIN, CHAPTER_MAX + 1):
        return (False, f"Chapter is either less than {CHAPTERS_MIN} or more than {CHAPTER_MAX}")
    return (True, chapter)


def validate_verses(verses: str) -> (bool, str):
    normalized = verses.strip()
    parts = normalized.split(',')

    for part in parts:
        part = part.strip()
        
        if not part:
            return (False, "Verse must be a number")

        if '-' in part:
            verse_parts = part.split('-')
            if len(verse_parts) != 2:
                return (False, "Invalid verse range format, use 'start-end'")
            
            if not verse_parts[0].strip() or not verse_parts[1].strip():
                return (False, "Invalid verse range format, use 'start-end'")

            try:
                start = int(verse_parts[0].strip())
                end = int(verse_parts[1].strip())
            except ValueError:
                return (False, "Verse numbers must be integers")
            
            if start < VERSES_MIN or end > VERSES_MAX:
                return (False, f"Verses must be in range {VERSES_MIN}-{VERSES_MAX}")
            if start > end:
                return (False, "Start verse must be less than end verse")
        
        else:
            try:
                verse_num = int(part)
            except ValueError:
                return (False, "Verse must be a number")
            
            if verse_num < VERSES_MIN or verse_num > VERSES_MAX:
                return (False, f"Verse must be in range {VERSES_MIN} - {VERSES_MAX}")
            
    return (True, normalized)


if __name__ == "__main__":
    result = validate_books("JOhn1")
    logger.debug(f"result: {result}")