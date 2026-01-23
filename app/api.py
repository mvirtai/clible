import json
import time
import requests
from loguru import logger
from pathlib import Path

from app.db.queries import QueryDB

mock_data_path = Path(__file__).resolve().parent.parent / "data" / "mock_data.json"

BASE_URL = "http://bible-api.com"


def calculate_max_chapter(book: str, translation: str | None = None) -> int | None:
    """
    Calculate the maximum chapter number in a book by attempting to fetch chapters
    and finding the highest valid chapter number.
    
    Uses a binary search approach: tries common chapter numbers first, then narrows down.
    Checks cache first before making API calls.
    
    Args:
        book: Book name (e.g., "Romans")
        translation: Translation identifier (default: "web")
        
    Returns:
        Maximum chapter number found in the book, or None if unable to determine
    """
    translation = translation.lower() if translation else "web"
    
    # Check cache first
    try:
        with QueryDB() as db:
            cached_max = db.get_cached_max_chapter(book, translation)
            if cached_max is not None:
                logger.info(f"Using cached max chapter for {book} ({translation}): {cached_max}")
                return cached_max
    except Exception as e:
        logger.warning(f"Failed to check cache for max chapter: {e}")
    
    translation_sentence = "?translation=" + translation
    
    # First verify book exists by trying chapter 1
    url = f"{BASE_URL}/{book}+1{translation_sentence}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            logger.warning(f"Book {book} chapter 1 not found, cannot calculate max chapter")
            return None
    except requests.exceptions.RequestException:
        logger.warning(f"Error checking {book} chapter 1, cannot calculate max chapter")
        return None
    
    # Try common high chapter numbers first (most books have < 50 chapters)
    # Check: 50, 30, 20, 10, then go up from there if needed
    test_chapters = [50, 30, 20, 10]
    max_found = 1
    
    for test_chapter in test_chapters:
        time.sleep(1)  # Rate limiting: 1 second delay between API calls
        url = f"{BASE_URL}/{book}+{test_chapter}{translation_sentence}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                verses = data.get("verses", [])
                if verses:
                    max_found = test_chapter
                    break
        except requests.exceptions.RequestException:
            continue
    
    # If we found a chapter >= 10, search upward from there
    if max_found >= 10:
        # Search upward from max_found to find the actual max
        for chapter_num in range(max_found + 1, 151):
            time.sleep(1)  # Rate limiting: 1 second delay between API calls
            url = f"{BASE_URL}/{book}+{chapter_num}{translation_sentence}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    verses = data.get("verses", [])
                    if verses:
                        max_found = chapter_num
                    else:
                        break
                else:
                    break
            except requests.exceptions.RequestException:
                break
    else:
        # If max_found < 10, search upward from 1
        for chapter_num in range(2, 11):
            time.sleep(1)  # Rate limiting: 1 second delay between API calls
            url = f"{BASE_URL}/{book}+{chapter_num}{translation_sentence}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    verses = data.get("verses", [])
                    if verses:
                        max_found = chapter_num
                    else:
                        break
                else:
                    break
            except requests.exceptions.RequestException:
                break
    
    logger.info(f"Calculated max chapter for {book}: {max_found}")
    
    # Cache the result
    try:
        with QueryDB() as db:
            db.set_cached_max_chapter(book, translation, max_found)
            logger.debug(f"Cached max chapter for {book} ({translation}): {max_found}")
    except Exception as e:
        logger.warning(f"Failed to cache max chapter: {e}")
    
    return max_found


def calculate_max_verse(book: str, chapter: str, translation: str | None = None) -> int | None:
    """
    Calculate the maximum verse number in a chapter by fetching the chapter and
    finding the highest verse number in the response.
    
    Checks cache first before making API calls.
    
    Args:
        book: Book name (e.g., "John")
        chapter: Chapter number (e.g., "3")
        translation: Translation identifier (default: "web")
        
    Returns:
        Maximum verse number found in the chapter, or None if unable to determine
    """
    translation = translation.lower() if translation else "web"
    
    # Check cache first
    try:
        chapter_num = int(chapter)
        with QueryDB() as db:
            cached_max = db.get_cached_max_verse(book, chapter_num, translation)
            if cached_max is not None:
                logger.info(f"Using cached max verse for {book} {chapter} ({translation}): {cached_max}")
                return cached_max
    except (ValueError, Exception) as e:
        logger.warning(f"Failed to check cache for max verse: {e}")
    
    translation_sentence = "?translation=" + translation
    url = f"{BASE_URL}/{book}+{chapter}{translation_sentence}"
    
    try:
        logger.debug(f"Fetching chapter to calculate max verse: {url}")
        time.sleep(1)  # Rate limiting: 1 second delay before API call
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        verses = data.get("verses", [])
        if not verses:
            logger.warning(f"No verses found in chapter {book} {chapter}")
            return None
        
        # Find the maximum verse number
        verse_numbers = [verse.get("verse", 0) for verse in verses if verse.get("verse")]
        if not verse_numbers:
            logger.warning(f"No valid verse numbers found in chapter {book} {chapter}")
            return None
        
        max_verse = max(verse_numbers)
        if max_verse <= 0:
            logger.warning(f"Invalid max verse calculated: {max_verse} for {book} {chapter}")
            return None
        
        logger.info(f"Calculated max verse for {book} {chapter}: {max_verse}")
        
        # Cache the result
        try:
            chapter_num = int(chapter)
            with QueryDB() as db:
                db.set_cached_max_verse(book, chapter_num, translation, max_verse)
                logger.debug(f"Cached max verse for {book} {chapter} ({translation}): {max_verse}")
        except (ValueError, Exception) as e:
            logger.warning(f"Failed to cache max verse: {e}")
        
        return max_verse
        
    except (requests.exceptions.RequestException, json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to calculate max verse for {book} {chapter}: {e}")
        return None


def fetch_book_list() -> list[str]:
    """Fetch a list of books from bible-api.com API"""
    url = f"{BASE_URL}/data/web"
    try:
        time.sleep(1)  # Rate limiting: 1 second delay before API call
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("books", [])
    except requests.exceptions.Timeout:
        logger.error(f"Request to {url} timed out")
        return []
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error when fetching {url}")
        return []
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        return []


def fetch_by_reference(
    book: str | None = None,
    chapter: str | None = None,
    verses: str | None = None,
    random: bool = False, 
    translation: str | None = None,
    use_mock: bool = False) -> dict:
    """Fetch a  verse, verses or a chapter from bible-api.com API"""

    # Possibility to use mock data for testing purposes
    if use_mock:
        logger.info(f"Using mock data from path {mock_data_path}")
        
        try:
            with open(mock_data_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            logger.error(f"Mock data file missing at {mock_data_path}")
            return None
        except json.JSONDecodeError as exc:
            logger.error(f"Invalid JSON in mock data: {exc}")
            return None
        return data
    
    translation = translation.lower() if translation else "web"
    translation_sentence = "?translation=" + translation
    
    # Handle chapter='all' - calculate max chapter for the book
    if chapter is not None and chapter.strip().lower() == "all":
        logger.info(f"'all' chapter specified, calculating max chapter for {book}")
        max_chapter = calculate_max_chapter(book, translation)
        if max_chapter:
            chapter = str(max_chapter)
            logger.info(f"Using calculated max chapter: {chapter}")
            time.sleep(1)  # Rate limiting: 1 second delay after calculating max chapter
        else:
            logger.error(f"Could not calculate max chapter for {book}")
            return None
    
    # Handle empty string or 'all' for verses - calculate max verse and fetch all verses
    if verses is not None and verses.strip().lower() in ("", "all"):
        if not chapter:
            logger.error("Cannot calculate max verse without a chapter")
            return None
        logger.info(f"Empty or 'all' verses specified, calculating max verse for {book} {chapter}")
        max_verse = calculate_max_verse(book, chapter, translation)
        if max_verse:
            verses = f"1-{max_verse}"
            logger.info(f"Using calculated verse range: {verses}")
        else:
            # Fallback to fetching entire chapter if max verse calculation fails
            logger.warning(f"Could not calculate max verse, fetching entire chapter instead")
            verses = None
    
    # Fetch a random verse
    if random:
        url = f"{BASE_URL}/data/random{translation_sentence}"
        logger.info(f"Fetching a random verse from path: {url}")
    # Fetch a single chapter
    elif not verses:
        url = f"{BASE_URL}/{book}+{chapter}{translation_sentence}"
        logger.info(f"Fetching a single chapter from path: {url}")
    # Fetch a single verse or multiple verses
    else:
        url = f"{BASE_URL}/{book}+{chapter}:{verses}{translation_sentence}"
        logger.info(f"Fetching a single verse or multiple verses from path: {url}")

    # API call
    try:
        time.sleep(1)  # Rate limiting: 1 second delay before API call
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        logger.info(f"Response status: {response.status_code}")

        #Transform random verse response to match the expected structure
        if random and data:
            random_verse = data.get('random_verse', {})
            translation = data.get('translation', {})

            # Build reference string
            book = random_verse.get('book', '')
            chapter = random_verse.get('chapter', '')
            verse = random_verse.get('verse', '')
            reference = f"{book} {chapter}:{verse}" if all([book, chapter, verse]) else 'Unknown reference'

            # Transform to standard format
            data = {
                "reference": reference,
                "verses": [{
                    "book_id": random_verse.get('book_id', ''),
                    "book_name": random_verse.get('book_name', ''),
                    "chapter": random_verse.get('chapter', 0),
                    "verse": random_verse.get('verse', 0),
                    "text": random_verse.get('text', ''),
                }],
                "translation_id": translation.get('identifier', ''),
                "translation_name": translation.get('name', ''),
                "translation_note": translation.get('license', ''),
            }

            logger.debug(f"Transformed random verse data: {json.dumps(data, indent=2) if data else 'None'}")
            return data
        
        return data

    except requests.exceptions.Timeout:
        logger.error(f"Request to {url} timed out")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error when fetching {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON response from {url}")
        return None

if __name__ == "__main__":
    books = fetch_book_list()
    for book in books:
        print(book["name"])