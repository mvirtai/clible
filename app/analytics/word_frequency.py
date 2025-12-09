from loguru import logger
from app.utils import console
import re

from app.db.queries import QueryDB


def analyze_word_frequency(verses: list[dict], top_n: int = 10) -> dict:
    pass


if __name__ == "__main__":
    # Initialize the database connection in a context manager
    with QueryDB() as db:
        # Display all saved queries to the user
        db.show_all_saved_queries()
        # Prompt the user to input a query ID
        query_id = input("Give ID: ").strip()
        # Retrieve verses matching the given query ID
        verse_data = db.get_verses_by_query_id(query_id)
        results = analyze_word_frequency(verse_data)
   
   