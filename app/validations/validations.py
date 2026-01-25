"""
Input validation for clible CLI.

Validates book references, chapter numbers, and verse ranges.
Uses validation_lists for allowed books.
"""

from app.validations.validation_lists import books_list

CHAPTERS_MIN = 1
CHAPTER_MAX = 150
VERSES_MIN = 1
VERSES_MAX = 175


def validate_books(book_ref: str) -> bool:
    """
    Validate book name against canonical list.

    Args:
        book_ref: Book name to validate

    Returns:
        True if book is valid, False otherwise
    """
    return book_ref.strip().lower() in books_list


def validate_chapter(chapter: str, allow_all: bool = True) -> tuple[bool, str]:
    """
    Validate chapter input.

    Args:
        chapter: Chapter string to validate
        allow_all: If True, 'all' keyword is accepted (default: True)

    Returns:
        Tuple of (is_valid, payload) where payload is either the validated chapter
        string or an error message string

    Note:
        Chapter must be a numeric value between CHAPTERS_MIN and CHAPTER_MAX,
        or 'all' (if allow_all=True) to fetch all chapters in the book.
        Empty strings are not allowed.
    """
    chapter = chapter.strip().lower()

    if not chapter:
        return (False, "Chapter cannot be empty. Please enter a chapter number.")

    if chapter == "all":
        if allow_all:
            return (True, "all")
        return (False, "Chapter cannot be 'all' in this context. Please enter a chapter number.")

    if not chapter.isnumeric():
        return (False, f"Chapter must be a numeric value between {CHAPTERS_MIN} and {CHAPTER_MAX}, or 'all'.")

    chapter_num = int(chapter)
    if chapter_num < CHAPTERS_MIN or chapter_num > CHAPTER_MAX:
        return (False, f"Chapter must be between {CHAPTERS_MIN} and {CHAPTER_MAX}.")

    return (True, chapter)


def validate_verses(verses: str, allow_empty: bool = False) -> tuple[bool, str]:
    """
    Validate verses input.

    Args:
        verses: Verses string to validate (e.g., "1", "1-3", "1,3,5", "1-3,5-7", "all")
        allow_empty: If True, empty string is considered valid (for entire chapter)

    Returns:
        Tuple of (is_valid, payload) where payload is either the validated verses
        string or an error message string

    Note:
        Verses can be:
        - Single verse: "1"
        - Range: "1-3"
        - Multiple verses: "1,3,5"
        - Mixed: "1-3,5-7"
        - "all" or empty (when allow_empty=True): fetches entire chapter
        All verse numbers must be between VERSES_MIN and VERSES_MAX.
    """
    normalized = verses.strip().lower()

    if normalized == "all":
        if allow_empty:
            return (True, "all")
        return (False, "Verse cannot be 'all' in this context. Please enter a verse number or range.")

    if not normalized:
        if allow_empty:
            return (True, "")
        return (False, "Verse cannot be empty. Please enter a verse number or range.")

    parts = normalized.split(',')

    for part in parts:
        part = part.strip()

        if not part:
            return (False, "Invalid verse format. Empty values are not allowed in verse lists.")

        if '-' in part:
            verse_parts = part.split('-')
            if len(verse_parts) != 2:
                return (False, "Invalid verse range format. Use 'start-end' (e.g., '1-3').")

            start_str = verse_parts[0].strip()
            end_str = verse_parts[1].strip()

            if not start_str or not end_str:
                return (False, "Invalid verse range format. Both start and end verses must be provided.")

            try:
                start = int(start_str)
                end = int(end_str)
            except ValueError:
                return (False, f"Verse numbers must be integers between {VERSES_MIN} and {VERSES_MAX}.")

            if start < VERSES_MIN or start > VERSES_MAX:
                return (False, f"Start verse must be between {VERSES_MIN} and {VERSES_MAX}.")
            if end < VERSES_MIN or end > VERSES_MAX:
                return (False, f"End verse must be between {VERSES_MIN} and {VERSES_MAX}.")
            if start > end:
                return (False, "Start verse must be less than or equal to end verse.")
        else:
            try:
                verse_num = int(part)
            except ValueError:
                return (False, f"Verse must be a number between {VERSES_MIN} and {VERSES_MAX}.")

            if verse_num < VERSES_MIN or verse_num > VERSES_MAX:
                return (False, f"Verse must be between {VERSES_MIN} and {VERSES_MAX}.")

    return (True, normalized)
