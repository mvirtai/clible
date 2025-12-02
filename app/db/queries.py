# app/db/queries.py

import sqlite3
from pathlib import Path
from datetime import datetime
from textwrap import shorten
from loguru import logger

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "clible.db"


class QueryDB:
    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS verses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                text TEXT NOT NULL,
                snippet TEXT,
                FOREIGN KEY (query_id) REFERENCES queries(id),
                FOREIGN KEY (book_id) REFERENCES books(id)
            );
            """
        )
        self.conn.commit()

    # ---------------------
    #   HELPERS
    # ---------------------

    def _ensure_book(self, book_name: str) -> int:
        self.cur.execute("SELECT id FROM books WHERE name = ?", (book_name,))
        row = self.cur.fetchone()

        if row:
            return row["id"]

        self.cur.execute("INSERT INTO books (name) VALUES (?)", (book_name,))
        self.conn.commit()
        return self.cur.lastrowid

    # ---------------------
    #   MAIN SAVE LOGIC
    # ---------------------

    def save_query(self, verse_data: dict) -> None:
        reference = verse_data.get("reference", "").strip()

        # 1. Save query metadata
        self.cur.execute(
            "INSERT INTO queries (reference) VALUES (?)",
            (reference,),
        )
        query_id = self.cur.lastrowid

        # 2. Extract verses
        verses = verse_data.get("verses", [])

        for v in verses:
            book_name = v.get("book_name")
            chapter = v.get("chapter")
            verse = v.get("verse")
            text = v.get("text")

            book_id = self._ensure_book(book_name)

            snippet = shorten(text.replace("\n", " "), width=160, placeholder="...")

            self.cur.execute(
                """
                INSERT INTO verses (
                    query_id, book_id, chapter, verse, text, snippet
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (query_id, book_id, chapter, verse, text, snippet),
            )

        self.conn.commit()
        logger.info(f"Saved query: {reference}")

    # ---------------------
    #   RETRIEVAL
    # ---------------------

    def show_all_saved_queries(self):
        self.cur.execute(
            """
            SELECT q.id, q.reference, q.created_at, COUNT(v.id) as verse_count
            FROM queries q
            LEFT JOIN verses v ON q.id = v.query_id
            GROUP BY q.id
            ORDER BY q.created_at DESC;
            """
        )
        rows = self.cur.fetchall()
        return [dict(row) for row in rows]

    # ---------------------
    #   ANALYTICS
    # ---------------------

    def search_word(self, word: str) -> list[dict]:
        pattern = f"%{word.lower()}%"

        self.cur.execute(
            """
            SELECT
                b.name as book,
                v.chapter,
                v.verse,
                v.text
            FROM verses v
            JOIN books b ON b.id = v.book_id
            WHERE LOWER(' ' || v.text || ' ') LIKE ?
            ORDER BY b.name, v.chapter, v.verse;
            """,
            (pattern,),
        )
        
        return [dict(row) for row in self.cur.fetchall()]


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
