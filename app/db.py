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
    

    def _build_snippet(self, reference: str, verses: list[str]) -> str:
        cleaned = [" ".join(v.get("text", "").split()) for v in verses]
        combined = " ".join(cleaned)
        text_snippet = shorten(combined, width=200, placeholder="...")
        return f"{reference}: {text_snippet}"


    def save_query(self, data: dict) -> None:
        reference = data.get('reference', 'Unknown reference').strip()
        verses = data.get('verses', [])
        snippet = self._build_snippet(reference, verses) if verses else f"{reference}: No verse text"

        full_text = " ".join([" ".join(v.get("text", "").split()) for v in verses]) if verses else "No verse text"

        timestamp = datetime.utcnow().isoformat()
        self.cur.execute(
        """
        INSERT INTO queries (query_text, result_snippet, created_at)
        VALUES (?, ?, ?)
        """,
        (full_text, snippet, timestamp)
    )
        logger.info(f"Saved verses from {reference} into database!")
        self.conn.commit()
        self.close()


    def show_all_saved_queries(self) -> list[dict]:
        self.cur.execute("SELECT * FROM queries")
        rows = self.cur.fetchall()
        return [dict(row) for row in rows]


    def close(self):
        self.conn.close()
        logger.info("Closed connection")


if __name__ == "__main__":
    # from app.api import fetch_verse_by_reference
    # verse_data = fetch_verse_by_reference(book='John', chapter='3', verses='16', use_mock=True)
    db = QueryDB()
    # reference = verse_data.get('reference', 'Unknown reference')
    # snippet = db._build_snippet(reference, verse_data.get('verses', []))
    # logger.info(f"Snippet: {snippet}")

    all_saved_verses = db.show_all_saved_queries()
    print(all_saved_verses)