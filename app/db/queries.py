# app/db/queries.py

import sqlite3
from pathlib import Path
from datetime import datetime
from textwrap import shorten
import uuid
from loguru import logger

DB_PATH = Path(__file__).resolve().parent / "clible.db"


# --- Schema for the database: ---
#
# Table: queries
#   - id (TEXT, PRIMARY KEY)
#   - reference (TEXT, NOT NULL)
#   - created_at (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)
#
# Table: books
#   - id (TEXT, PRIMARY KEY)
#   - name (TEXT, NOT NULL, UNIQUE)
#
# Table: verses
#   - id (TEXT, PRIMARY KEY)
#   - query_id (TEXT, NOT NULL, REFERENCES queries(id))
#   - book_id (TEXT, NOT NULL, REFERENCES books(id))
#   - chapter (INTEGER, NOT NULL)
#   - verse (INTEGER, NOT NULL)
#   - text (TEXT, NOT NULL)
#   - snippet (TEXT)
#
# Table: translations
#   - id (TEXT, PRIMARY KEY)
#   - abbr (TEXT, NOT NULL, UNIQUE)
#   - name (TEXT, NOT NULL, UNIQUE)
#   - note (TEXT)
#
#   FOREIGN KEY (query_id) REFERENCES queries(id)
#   FOREIGN KEY (book_id) REFERENCES books(id)


class QueryDB:
    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cur.execute("PRAGMA foreign_keys = ON;")
        self.cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS queries (
                id TEXT PRIMARY KEY,
                reference TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                translation_id TEXT,
                FOREIGN KEY (translation_id) REFERENCES translations(id)
            );

            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS verses (
                id TEXT PRIMARY KEY,
                query_id TEXT NOT NULL,
                book_id TEXT NOT NULL, 
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                text TEXT NOT NULL,
                snippet TEXT,
                FOREIGN KEY (query_id) REFERENCES queries(id),
                FOREIGN KEY (book_id) REFERENCES books(id)
            );

            CREATE TABLE IF NOT EXISTS translations (
                id TEXT PRIMARY KEY,
                abbr TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL UNIQUE,
                note TEXT NULL
            );
            """
        )
        self._create_user_tables()
        self.conn.commit()


        # add translations col
        try:
            self.cur.execute("ALTER TABLE queries ADD COLUMN translation_id TEXT REFERENCES translations(id)")
        except sqlite3.OperationalError:
            # if exists, ignore
            pass


    def _create_user_tables(self):
        self.cur.executescript(
            """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT,
                    scope TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    is_saved INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                -- junction table
                CREATE TABLE IF NOT EXISTS session_queries (
                    session_id TEXT NOT NULL,
                    query_id TEXT NOT NULL,
                    PRIMARY KEY (session_id, query_id),
                    FOREIGN KEY (session_id) REFERENCES sessions(id),
                    FOREIGN KEY (query_id) REFERENCES queries(id)
                );
                -- for temporary sessions
                CREATE TABLE IF NOT EXISTS session_queries_cache (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,  -- temporary session identifier
                    reference TEXT NOT NULL,
                    verse_data TEXT, -- JSON serialized verse data
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """
        )
        self.conn.commit()


    # ---------------------
    #   HELPERS
    # ---------------------

    def _ensure_book(self, book_name: str) -> str:
        self.cur.execute("SELECT id FROM books WHERE name = ?", (book_name,))
        row = self.cur.fetchone()

        if row:
            return row["id"]

        book_id = str(uuid.uuid4())[:8]
        self.cur.execute("INSERT INTO books (id, name) VALUES (?, ?)", (book_id, book_name))
        self.conn.commit()
        return book_id
    

    #----------------------
    #   USERS
    #----------------------

    def create_user(self, name: str) -> str | None:
        user_id = str(uuid.uuid4())[:8]
        if name and user_id:
            self.cur.execute("INSERT INTO users (id, name) VALUES (?, ?)",
                            (user_id, name)
            )
            self.conn.commit()
            return user_id
        return None
    

    def get_user_by_name(self, user_name: str) -> dict | None:
        if user_name:
            self.cur.execute("SELECT id, name, created_at FROM users WHERE name = ?", (user_name,))
            row = self.cur.fetchone()

            if row:
                return dict(row)
            else:
                new_user_id = self.create_user(user_name)
                return self.get_user_by_id(new_user_id)                


    def get_user_by_id(self, user_id: str) -> dict | None:
        if user_id:
            self.cur.execute("SELECT id, name, created_at FROM users WHERE id = ?", (user_id,))
            row = self.cur.fetchone()

            if row:
                return dict(row)
            return None


    def list_users(self) -> list[dict]:
        self.cur.execute("""
        SELECT u.id, u.name, u.created_at 
        FROM users u 
        ORDER BY u.created_at DESC
        LIMIT 100;
        """)
        rows = self.cur.fetchall()
        return [dict(r) for r in rows]
    

    def get_or_create_default_user(self) -> str:
        default_user = self.get_user_by_name("default")
        if default_user:
            return default_user.get("id")
        else:
            default_user_id = self.create_user("default")
            if default_user_id:
                return default_user_id
            else:
                logger.error("Failed to create default user.")
                raise Exception("Failed to create default user.")

    # ---------------------
    #   SESSION LOGIC
    # ---------------------



    # ---------------------
    #   MAIN SAVE LOGIC
    # ---------------------

    def save_query(self, verse_data: dict) -> None:
        reference = verse_data.get("reference", "").strip()

        # 1. Save query metadata
        query_id = str(uuid.uuid4())[:8]
        
        # Refactor to save translation metadata with query
        translation_id = None
        translation_name = verse_data.get("translation_name")
        translation_abbr = verse_data.get("translation_id")

        # translation_language is not provided in mock_data.json
        translation_language = None

        if translation_name or translation_abbr:
            # Check if translation already exists (ignore language field)
            self.cur.execute(
                "SELECT id FROM translations WHERE name = ? AND abbr = ?",
                (translation_name, translation_abbr)
            )
            translation_row = self.cur.fetchone()
            if translation_row:
                translation_id = translation_row["id"]
            else:
                translation_id = str(uuid.uuid4())[:8]
                self.cur.execute(
                    "INSERT INTO translations (id, name, abbr) VALUES (?, ?, ?)",
                    (translation_id, translation_name, translation_abbr)
                )
                self.conn.commit()

        # Save query with translation_id
        self.cur.execute(
            """
            INSERT INTO queries (id, reference, translation_id) VALUES (?, ?, ?)
            """, (query_id, reference, translation_id)
        )
        self.conn.commit()

        # 2. Extract verses
        verses = verse_data.get("verses", [])

        for v in verses:
            book_name = v.get("book_name")
            chapter = v.get("chapter")
            verse = v.get("verse")
            text = v.get("text")

            book_id = self._ensure_book(book_name)

            snippet = shorten(text.replace("\n", " "), width=160, placeholder="...")
            
            verse_id = str(uuid.uuid4())[:8]
            self.cur.execute(
                """
                INSERT INTO verses (
                    id, query_id, book_id, chapter, verse, text, snippet
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (verse_id, query_id, book_id, chapter, verse, text, snippet),
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
    

    def get_single_saved_query(self, query_id: str) -> dict | None:
        # 1. Get query metadata with translation info
        self.cur.execute(
            """
            SELECT
                q.id,
                q.reference,
                q.created_at,
                t.id as translation_id,
                t.abbr as translation_abbr,
                t.name as translation_name,
                t.note as translation_note
            FROM queries q
            LEFT JOIN translations t ON q.translation_id = t.id
            WHERE q.id = ?
            """,
            (query_id,)
        )
        query_row = self.cur.fetchone()

        if not query_row:
            return None
        
        # 2. Get verses
        self.cur.execute(
            """
            SELECT
                b.name as book_name,
                v.chapter,
                v.verse,
                v.text
            FROM verses v
            JOIN books b ON v.book_id = b.id
            WHERE v.query_id = ?
            ORDER BY v.chapter, v.verse
            """, (query_id,)
        )
        verses = [dict(row) for row in self.cur.fetchall()]

        # 3. Format the dictionary to match the structure of API-fetched data
        result = {
            "id": query_row["id"],
            "reference": query_row["reference"],
            "created_at": query_row["created_at"],
            "verses": verses,
        }
        
        # Add translation info if it exists
        if query_row["translation_id"]:
            result["translation_id"] = query_row["translation_abbr"]
            result["translation_name"] = query_row["translation_name"]
            if query_row["translation_note"]:
                result["translation_note"] = query_row["translation_note"]
        
        return result

    def get_verses_by_query_id(self, query_id: str) -> list[dict]:
        return self.get_single_saved_query(query_id)["verses"]

    # ---------------------
    #   RESET DATABASE
    # ---------------------

    def _reset_database(self):
        self.cur.executescript(
            """
            DROP TABLE IF EXISTS queries;
            DROP TABLE IF EXISTS books;
            DROP TABLE IF EXISTS verses;
            DROP TABLE IF EXISTS translations;
            """
        )

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

    def get_total_verse_count(self) -> int:
        """
        Get the total count of all saved verses.
        
        Returns:
            Total number of verses in the database.
        """
        self.cur.execute("SELECT COUNT(*) as count FROM verses")
        row = self.cur.fetchone()
        return row["count"] if row else 0

    def get_unique_books(self) -> list[str]:
        """
        Get a list of all unique book names.
        
        Returns:
            List of unique book names.
        """
        self.cur.execute("SELECT DISTINCT name FROM books ORDER BY name")
        rows = self.cur.fetchall()
        return [row["name"] for row in rows]

    def get_unique_chapters(self) -> list[tuple[str, int]]:
        """
        Get a list of all unique (book_name, chapter) pairs.
        
        Returns:
            List of tuples (book_name, chapter).
        """
        self.cur.execute(
            """
            SELECT DISTINCT b.name as book_name, v.chapter
            FROM verses v
            JOIN books b ON v.book_id = b.id
            ORDER BY b.name, v.chapter
            """
        )
        rows = self.cur.fetchall()
        return [(row["book_name"], row["chapter"]) for row in rows]

    def get_book_distribution(self) -> list[tuple[str, int]]:
        """
        Get book distribution (book name and verse count).
        
        Returns:
            List of tuples (book_name, count) sorted by count descending.
        """
        self.cur.execute(
            """
            SELECT b.name as book_name, COUNT(v.id) as count
            FROM verses v
            JOIN books b ON v.book_id = b.id
            GROUP BY b.name
            ORDER BY count DESC
            """
        )
        rows = self.cur.fetchall()
        return [(row["book_name"], row["count"]) for row in rows]

    def get_chapter_distribution(self) -> list[tuple[str, int, int]]:
        """
        Get chapter distribution (book name, chapter, verse count).
        
        Returns:
            List of tuples (book_name, chapter, count) sorted by count descending.
        """
        self.cur.execute(
            """
            SELECT b.name as book_name, v.chapter, COUNT(v.id) as count
            FROM verses v
            JOIN books b ON v.book_id = b.id
            GROUP BY b.name, v.chapter
            ORDER BY count DESC, b.name, v.chapter
            """
        )
        rows = self.cur.fetchall()
        return [(row["book_name"], row["chapter"], row["count"]) for row in rows]


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()


if __name__ == "__main__":
    db = QueryDB()
    db._reset_database()