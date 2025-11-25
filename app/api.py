import json
import requests
from loguru import logger
from pathlib import Path

mock_data_path = Path.home() / "clible" / "app" / "data" / "mock_data.json"


BASE_URL = "http://bible-api.com"


def fetch_verse_by_reference(book: str, chapter: str, verses: str) -> dict:
    use_mock = True

    if use_mock:
        logger.info(f"Using mock data from path {mock_data_path}")
        
        with open(mock_data_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        
        logger.info(f"File's type: {type(data)}")
        print(data)

    else:

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


if __name__ == "__main__":
    
    fetch_verse_by_reference(book="John", chapter="3", verses="16")