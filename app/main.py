import json
import requests
import pathlib
from loguru import logger


BASE_URL = "http://bible-api.com"


def get_ref_values() -> tuple[str, str, str]:
    book = input("Book: ").strip().lower()
    chapter = input("Chapter: ").strip()
    verses = input("Verse(s): ").strip()
    return book, chapter, verses


def format_url(book: str, chapter: str, verses: str) -> str:
    return f"https://bible-api.com/{book}+{chapter}:{verses}"


def fetch_verse_by_reference(book: str, chapter: str, verses: str) -> dict:
    url = f"{BASE_URL}/{book}+{chapter}:{verses}"
    logger.info(f"Fetching data from {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Heittää HTTPError, jos status code ei ole 2xx

        data = response.json()
        logger.info(f"Succesfully fetched verse: {data.get('reference', 'unknown')}")
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


def main():
    ref_tuple = get_ref_values()
    verse_data = fetch_verse_by_reference(*ref_tuple)

    if verse_data:
        print(json.dumps(verse_data, indent=2))
    else:
        print("Failed to fetch verse. Check logs for details.")
   

if __name__ == "__main__":
    main()