import json
import requests
from loguru import logger
from pathlib import Path

mock_data_path = Path(__file__).resolve().parent / "data" / "mock_data.json"


BASE_URL = "http://bible-api.com"


def fetch_by_reference(book: str, chapter: str, verses: str | None, use_mock: bool = False) -> dict:
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
    

    # Fetch a single chapter
    if not verses:
        url = f"{BASE_URL}/{book}+{chapter}"
        logger.info(f"Fetching a single chapter from path: {url}")
    # Fetch a single verse or multiple verses
    else:
        url = f"{BASE_URL}/{book}+{chapter}:{verses}"
        logger.info(f"Fetching a single verse or multiple verses from path: {url}")

    # API call
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        logger.info(f"Response status: {response.status_code}")
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