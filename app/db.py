import sqlite3
from pathlib import Path
from loguru import logger
from datetime import datetime
from textwrap import shorten

from app.api import fetch_verse_by_reference

db_path = Path(__file__).resolve().parent / "data" / "clible.db"

class QueryDB:
    def __init__(self, db_path: str = db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                result_snippet TEXT NOT NULL,
                created_at TIMESTAMP
            )
        """)
    

    def _build_snippet(self, verses: list[str]) -> str:
        cleaned = [" ".join(v.get("text", "").split()) for v in verses]
        combined = " ".join(cleaned)
        return shorten(combined, width=200, placeholder="...")


    def save_query(self, data: dict) -> None:
        reference = data.get('reference', 'Unknown reference').strip()
        verses = data.get('verses', [])
        snippet = self.build_snippet(verses) if verses else 'No verse text'
        timestamp = datetime.utcnow().isoformat()

        self.cur.execute(
        """
        INSERT INTO queries (query_text, result_snippet, created_at)
        VALUES (?, ?, ?)
        """,
        (reference, snippet, timestamp)
    )
        self.conn.commit()


if __name__ == "__main__":
    from app.api import fetch_verse_by_reference
    verse_data = fetch_verse_by_reference(use_mock=True, output='text')
    db = QueryDB()
    snippet = db._build_snippet(verse_data.get('verses', []))
    logger.info(f"Snippet: {snippet}")