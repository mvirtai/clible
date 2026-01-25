"""
SQLite database layer for clible.

Provides QueryDB for queries, verses, sessions, users, and analysis history.
Schema: core (translations, books, users), query (queries, verses),
session (sessions, session_queries, session_queries_cache), analysis
(analysis_history, analysis_results).
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from textwrap import shorten

from loguru import logger

from app.ui import console

DB_PATH = Path(__file__).resolve().parent / "clible.db"


class QueryDB:
    """
    Database interface for clible.

    Manages SQLite database operations for queries, verses, sessions, users,
    and analysis history. Provides context manager support for automatic cleanup.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database: enable foreign keys and create all tables."""
        self.cur.execute("PRAGMA foreign_keys = ON;")
        self._create_all_tables()
        self.conn.commit()

    def _create_all_tables(self):
        """
        Create all database tables in correct dependency order.

        Tables are created in this order to respect foreign key constraints:
        1. Core independent tables
        2. Tables depending on core tables
        3. Junction/relationship tables
        4. Analysis tables
        """
        self._create_core_tables()
        self._create_query_tables()
        self._create_session_tables()
        self._create_analysis_tables()

    def _create_core_tables(self):
        """Create core independent tables (no foreign key dependencies)."""
        self.cur.executescript("""
            CREATE TABLE IF NOT EXISTS translations (
                id TEXT PRIMARY KEY,
                abbr TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL UNIQUE,
                note TEXT NULL
            );

            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS book_chapter_cache (
                book_name TEXT NOT NULL,
                translation TEXT NOT NULL,
                max_chapter INTEGER NOT NULL,
                last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (book_name, translation)
            );

            CREATE TABLE IF NOT EXISTS book_verse_cache (
                book_name TEXT NOT NULL,
                chapter INTEGER NOT NULL,
                translation TEXT NOT NULL,
                max_verse INTEGER NOT NULL,
                last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (book_name, chapter, translation)
            );
        """)

    def _create_query_tables(self):
        """Create tables for storing queries and verses."""
        self.cur.executescript("""
            CREATE TABLE IF NOT EXISTS queries (
                id TEXT PRIMARY KEY,
                reference TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                translation_id TEXT,
                FOREIGN KEY (translation_id) REFERENCES translations(id)
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
        """)

    def _create_session_tables(self):
        """Create tables for user sessions and session-query relationships."""
        self.cur.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT,
                scope TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_saved INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS session_queries (
                session_id TEXT NOT NULL,
                query_id TEXT NOT NULL,
                PRIMARY KEY (session_id, query_id),
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (query_id) REFERENCES queries(id)
            );

            CREATE TABLE IF NOT EXISTS session_queries_cache (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                reference TEXT NOT NULL,
                verse_data TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

    def _create_analysis_tables(self):
        """Create tables for storing analysis history and results."""
        self.cur.executescript("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                session_id TEXT,
                user_name TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                scope_type TEXT NOT NULL,
                scope_details TEXT,
                verse_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS analysis_results (
                id TEXT PRIMARY KEY,
                analysis_id TEXT NOT NULL,
                result_type TEXT NOT NULL,
                result_data TEXT NOT NULL,
                chart_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analysis_history(id)
            );

            CREATE INDEX IF NOT EXISTS idx_analysis_user ON analysis_history(user_id);
            CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis_history(analysis_type);
            CREATE INDEX IF NOT EXISTS idx_analysis_session ON analysis_history(session_id);
            CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_history(created_at);
            CREATE INDEX IF NOT EXISTS idx_results_analysis ON analysis_results(analysis_id);
        """)

    def _reset_database(self):
        """
        Reset entire database by dropping all tables.

        Tables are dropped in reverse dependency order:
        - Child tables (with foreign keys) first
        - Parent tables last
        """
        self.cur.executescript("""
            DROP TABLE IF EXISTS analysis_results;
            DROP TABLE IF EXISTS session_queries;
            DROP TABLE IF EXISTS session_queries_cache;
            DROP TABLE IF EXISTS verses;
            DROP TABLE IF EXISTS analysis_history;
            DROP TABLE IF EXISTS sessions;
            DROP TABLE IF EXISTS queries;
            DROP TABLE IF EXISTS books;
            DROP TABLE IF EXISTS translations;
            DROP TABLE IF EXISTS users;
        """)
        self._create_all_tables()
        self.conn.commit()

    def _ensure_book(self, book_name: str) -> str:
        """Get or create a book by name. Returns book ID."""
        self.cur.execute("SELECT id FROM books WHERE name = ?", (book_name,))
        row = self.cur.fetchone()

        if row:
            return row["id"]

        book_id = str(uuid.uuid4())[:8]
        self.cur.execute("INSERT INTO books (id, name) VALUES (?, ?)", (book_id, book_name))
        self.conn.commit()
        return book_id

    def _serialize_verse_data(self, verse_data: dict) -> str:
        """Serialize verse data to JSON string."""
        return json.dumps(verse_data, ensure_ascii=False)

    def _deserialize_verse_data(self, data_text: str) -> dict:
        """Deserialize JSON string to verse data dictionary."""
        try:
            return json.loads(data_text)
        except (json.JSONDecodeError, TypeError):
            return {}

    def create_user(self, name: str) -> str | None:
        """Create a new user. Returns user ID or None if failed."""
        user_id = str(uuid.uuid4())[:8]
        if name and user_id:
            self.cur.execute("INSERT INTO users (id, name) VALUES (?, ?)",
                            (user_id, name)
            )
            self.conn.commit()
            return user_id
        return None

    def get_user_by_name(self, user_name: str) -> dict | None:
        """Get user by name. Creates user if doesn't exist."""
        if user_name:
            self.cur.execute("SELECT id, name, created_at FROM users WHERE name = ?", (user_name,))
            row = self.cur.fetchone()

            if row:
                return dict(row)
            else:
                self.create_user(user_name)
                return self.get_user_by_name(user_name)
        return None

    def get_user_by_id(self, user_id: str) -> dict | None:
        """Get user by ID. Returns None if not found."""
        if user_id:
            self.cur.execute("SELECT id, name, created_at FROM users WHERE id = ?", (user_id,))
            row = self.cur.fetchone()

            if row:
                return dict(row)
            return None

    def list_users(self) -> list[dict]:
        """List all users, ordered by creation date (newest first)."""
        self.cur.execute("""
        SELECT u.id, u.name, u.created_at
        FROM users u
        ORDER BY u.created_at DESC
        LIMIT 100;
        """)
        rows = self.cur.fetchall()
        return [dict(r) for r in rows]

    def get_or_create_default_user(self, user_name: str = "default") -> str:
        """
        Get or create a user by name.

        Args:
            user_name: Username to get or create (default: "default")

        Returns:
            User ID if successful, None if failed
        """
        default_user = self.get_user_by_name(user_name)
        if default_user:
            return default_user.get("id")
        else:
            default_user_id = self.create_user(user_name)
            if default_user_id:
                return default_user_id
            else:
                logger.error(f"Failed to create user: {user_name}")
                return None

    def create_session(self, user_id: str, name: str, scope: str, is_temporary: bool = False) -> str | None:
        """Create a new session. Returns session ID or None if failed."""
        session_id = str(uuid.uuid4())[:8]
        if session_id and user_id:
            self.cur.execute(
                "INSERT INTO sessions (id, user_id, name, scope, is_saved) VALUES (?, ?, ?, ?, ?)",
                (
                    session_id,
                    user_id,
                    name,
                    scope,
                    0 if is_temporary else 1,
                ),
            )
            self.conn.commit()
            return session_id
        return None

    def get_session(self, session_id: str) -> dict | None:
        """Get session by ID. Returns None if not found."""
        if not session_id:
            return None
        self.cur.execute(
            "SELECT id, user_id, name, scope, created_at, is_saved FROM sessions WHERE id = ?",
            (session_id,),
        )
        row = self.cur.fetchone()
        return dict(row) if row else None

    def list_sessions(self, user_id: str | None = None) -> list[dict]:
        """List sessions, optionally filtered by user_id."""
        sql = "SELECT id, user_id, name, scope, created_at, is_saved FROM sessions"
        params: tuple[str, ...] = ()
        if user_id:
            sql += " WHERE user_id = ?"
            params = (user_id,)
        sql += " ORDER BY created_at DESC"
        self.cur.execute(sql, params)
        rows = self.cur.fetchall()
        return [dict(r) for r in rows]

    def add_query_to_session(self, session_id: str, query_id: str) -> None:
        """Link a query to a session. Silently ignores if already linked."""
        if not (session_id and query_id):
            return

        try:
            self.cur.execute(
                "INSERT INTO session_queries (session_id, query_id) VALUES (?, ?)",
                (session_id, query_id),
            )
            self.conn.commit()
            logger.info(f"Result saved and linked to session {session_id}")
            console.print(f"[green]Result saved and linked to session {session_id}[/green]")
        except sqlite3.IntegrityError:
            logger.debug("Query %s already linked to session %s", query_id, session_id)

    def save_query_to_session_cache(self, session_id: str, verse_data: dict) -> str | None:
        """Save query data to session cache. Returns cache entry ID."""
        query_id = str(uuid.uuid4())[:8]
        reference = verse_data.get("reference", "").strip()
        if not session_id or not query_id:
            return None
        serialized = self._serialize_verse_data(verse_data)
        self.cur.execute(
            "INSERT INTO session_queries_cache (id, session_id, reference, verse_data) VALUES (?, ?, ?, ?)",
            (query_id, session_id, reference, serialized),
        )
        self.conn.commit()
        return query_id

    def get_cached_queries_for_session(self, session_id: str) -> list[dict]:
        """Get all cached queries for a session."""
        if not session_id:
            return []
        self.cur.execute(
            "SELECT id, reference, verse_data, created_at FROM session_queries_cache WHERE session_id = ?",
            (session_id,),
        )
        rows = self.cur.fetchall()
        return [
            {
                "id": row["id"],
                "reference": row["reference"],
                "verse_data": self._deserialize_verse_data(row["verse_data"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def get_session_queries(self, session_id: str) -> list[dict]:
        """Get all queries for a session (both saved and cached)."""
        results: list[dict] = []
        if not session_id:
            return results
        self.cur.execute(
            "SELECT query_id FROM session_queries WHERE session_id = ?", (session_id,)
        )
        for row in self.cur.fetchall():
            query_id = row.get("query_id")
            if query_id:
                query_data = self.get_single_saved_query(query_id)
                if query_data:
                    query_data["_source"] = "saved"
                    results.append(query_data)
        cached = self.get_cached_queries_for_session(session_id)
        for row in cached:
            row["_source"] = "cache"
            results.append(row)
        return results

    def save_session(self, session_id: str) -> None:
        """Mark a session as saved."""
        if not session_id:
            return
        self.cur.execute(
            "UPDATE sessions SET is_saved = 1 WHERE id = ?", (session_id,)
        )
        self.conn.commit()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its related data."""
        if not session_id:
            return False
        self.cur.execute("DELETE FROM session_queries WHERE session_id = ?", (session_id,))
        self.cur.execute("DELETE FROM session_queries_cache WHERE session_id = ?", (session_id,))
        self.cur.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self.conn.commit()
        return self.cur.rowcount > 0

    def clear_session_cache(self, session_id: str) -> bool:
        """Clear cached queries for a session."""
        if not session_id:
            return False
        self.cur.execute("DELETE FROM session_queries_cache WHERE session_id = ?", (session_id,))
        self.conn.commit()
        return self.cur.rowcount > 0

    def save_query(self, verse_data: dict) -> str:
        """Save a query with its verses to the database. Returns query ID."""
        reference = verse_data.get("reference", "").strip()

        query_id = str(uuid.uuid4())[:8]

        translation_id = None
        translation_name = verse_data.get("translation_name")
        translation_abbr = verse_data.get("translation_id")

        if translation_name or translation_abbr:
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

        self.cur.execute(
            """
            INSERT INTO queries (id, reference, translation_id) VALUES (?, ?, ?)
            """, (query_id, reference, translation_id)
        )
        self.conn.commit()

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
        return query_id

    def show_all_saved_queries(self):
        """List all saved queries with verse counts."""
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
        """Get a single query with all its verses and translation info."""
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

        result = {
            "id": query_row["id"],
            "reference": query_row["reference"],
            "created_at": query_row["created_at"],
            "verses": verses,
        }

        if query_row["translation_id"]:
            result["translation_id"] = query_row["translation_abbr"]
            result["translation_name"] = query_row["translation_name"]
            if query_row["translation_note"]:
                result["translation_note"] = query_row["translation_note"]

        return result

    def get_verses_by_query_id(self, query_id: str) -> list[dict]:
        """Get verses for a specific query ID. Returns empty list if query not found."""
        query_data = self.get_single_saved_query(query_id)
        if query_data:
            return query_data.get("verses", [])
        return []

    def get_saved_query_by_reference(self, reference: str, translation: str | None = None) -> dict | None:
        """
        Get a saved query by reference and optionally by translation.

        Args:
            reference: Verse reference string (e.g., "John 3:16")
            translation: Optional translation identifier (e.g., "web")

        Returns:
            Query data dictionary matching the structure of API-fetched data, or None if not found
        """
        if not reference:
            return None

        logger.info(f"get_saved_query_by_reference: looking for '{reference}', translation: '{translation}'")

        sql = """
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
            WHERE q.reference = ?
        """
        params: tuple = (reference,)

        if translation:
            sql += " AND LOWER(t.abbr) = ?"
            params = (reference, translation.lower())

        logger.info(f"Executing SQL: {sql} with params: {params}")
        self.cur.execute(sql, params)
        query_row = self.cur.fetchone()

        if not query_row:
            logger.info(f"No saved query found for '{reference}'")
            return None

        logger.info(f"Found saved query: id={query_row['id']}, reference={query_row['reference']}, translation_abbr={query_row.get('translation_abbr')}")

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
            """, (query_row["id"],)
        )
        verses = [dict(row) for row in self.cur.fetchall()]

        result = {
            "reference": query_row["reference"],
            "verses": verses,
        }

        if query_row["translation_id"]:
            result["translation_id"] = query_row["translation_abbr"]
            result["translation_name"] = query_row["translation_name"]
            if query_row["translation_note"]:
                result["translation_note"] = query_row["translation_note"]

        return result

    def get_cached_query_by_reference(self, reference: str, translation: str | None = None, session_id: str | None = None) -> dict | None:
        """
        Get a cached query from session cache by reference and optionally by translation.

        Checks all session caches if session_id is not provided, or only the specified session.

        Args:
            reference: Verse reference string (e.g., "John 3:16")
            translation: Optional translation identifier (e.g., "web")
            session_id: Optional session ID to limit search to specific session

        Returns:
            Cached query data dictionary, or None if not found
        """
        if not reference:
            return None

        logger.info(f"get_cached_query_by_reference: looking for '{reference}', translation: '{translation}', session_id: '{session_id}'")

        sql = """
            SELECT id, reference, verse_data, created_at, session_id
            FROM session_queries_cache
            WHERE reference = ?
        """
        params: tuple = (reference,)

        if session_id:
            sql += " AND session_id = ?"
            params = (reference, session_id)

        sql += " ORDER BY created_at DESC LIMIT 1"

        logger.info(f"Executing SQL: {sql} with params: {params}")
        self.cur.execute(sql, params)
        row = self.cur.fetchone()

        if not row:
            logger.info(f"No cached query found for '{reference}'")
            return None

        logger.info(f"Found cached query: id={row['id']}, reference={row['reference']}, session_id={row['session_id']}")
        verse_data = self._deserialize_verse_data(row["verse_data"])

        if translation:
            verse_translation = verse_data.get("translation_id", "").lower()
            logger.info(f"Comparing translations: verse_translation='{verse_translation}', requested='{translation.lower()}'")
            if verse_translation != translation.lower():
                logger.info(f"Translation mismatch, returning None")
                return None

        logger.info(f"Returning cached query data")
        return verse_data

    def search_word(self, word: str) -> list[dict]:
        """Search for a word in all verses."""
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
        """Get the total count of all saved verses."""
        self.cur.execute("SELECT COUNT(*) as count FROM verses")
        row = self.cur.fetchone()
        return row["count"] if row else 0

    def get_unique_books(self) -> list[str]:
        """Get a list of all unique book names."""
        self.cur.execute("SELECT DISTINCT name FROM books ORDER BY name")
        rows = self.cur.fetchall()
        return [row["name"] for row in rows]

    def get_unique_chapters(self) -> list[tuple[str, int]]:
        """Get a list of all unique (book_name, chapter) pairs."""
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
        """Get book distribution (book name and verse count)."""
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
        """Get chapter distribution (book name, chapter, verse count)."""
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

    def get_verses_by_book(self, book_name: str) -> list[dict]:
        """Get all verses for a specific book name."""
        self.cur.execute(
            """
            SELECT
                b.name as book_name,
                v.chapter,
                v.verse,
                v.text
            FROM verses v
            JOIN books b ON v.book_id = b.id
            WHERE b.name = ?
            ORDER BY v.chapter, v.verse
            """,
            (book_name,)
        )
        return [dict(row) for row in self.cur.fetchall()]

    def get_all_verses_from_session(self, session_id: str) -> list[dict]:
        """Get all verses from all queries in a session (both saved and cached)."""
        all_verses = []

        self.cur.execute(
            """
            SELECT DISTINCT v.id, b.name as book_name, v.chapter, v.verse, v.text
            FROM session_queries sq
            JOIN verses v ON sq.query_id = v.query_id
            JOIN books b ON v.book_id = b.id
            WHERE sq.session_id = ?
            ORDER BY b.name, v.chapter, v.verse
            """,
            (session_id,)
        )
        all_verses.extend([dict(row) for row in self.cur.fetchall()])

        cached = self.get_cached_queries_for_session(session_id)
        for cached_query in cached:
            verse_data = cached_query.get('verse_data', {})
            verses = verse_data.get('verses', [])
            all_verses.extend(verses)

        return all_verses

    def get_verses_from_multiple_queries(self, query_ids: list[str]) -> list[dict]:
        """Get all verses from multiple query IDs."""
        if not query_ids:
            return []

        placeholders = ','.join('?' * len(query_ids))
        self.cur.execute(
            f"""
            SELECT DISTINCT
                b.name as book_name,
                v.chapter,
                v.verse,
                v.text
            FROM verses v
            JOIN books b ON v.book_id = b.id
            WHERE v.query_id IN ({placeholders})
            ORDER BY b.name, v.chapter, v.verse
            """,
            query_ids
        )
        return [dict(row) for row in self.cur.fetchall()]

    def get_cached_max_chapter(self, book_name: str, translation: str) -> int | None:
        """
        Get cached max chapter for a book and translation.

        Args:
            book_name: Name of the book (e.g., "John")
            translation: Translation identifier (e.g., "web")

        Returns:
            Cached max chapter number, or None if not found
        """
        self.cur.execute(
            """
            SELECT max_chapter FROM book_chapter_cache
            WHERE book_name = ? AND translation = ?
            """,
            (book_name, translation.lower())
        )
        row = self.cur.fetchone()
        return row["max_chapter"] if row else None

    def set_cached_max_chapter(self, book_name: str, translation: str, max_chapter: int) -> None:
        """
        Cache max chapter for a book and translation.

        Args:
            book_name: Name of the book (e.g., "John")
            translation: Translation identifier (e.g., "web")
            max_chapter: Maximum chapter number to cache
        """
        self.cur.execute(
            """
            INSERT OR REPLACE INTO book_chapter_cache
            (book_name, translation, max_chapter, last_updated)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (book_name, translation.lower(), max_chapter)
        )
        self.conn.commit()

    def get_cached_max_verse(self, book_name: str, chapter: int, translation: str) -> int | None:
        """
        Get cached max verse for a book, chapter, and translation.

        Args:
            book_name: Name of the book (e.g., "John")
            chapter: Chapter number
            translation: Translation identifier (e.g., "web")

        Returns:
            Cached max verse number, or None if not found
        """
        self.cur.execute(
            """
            SELECT max_verse FROM book_verse_cache
            WHERE book_name = ? AND chapter = ? AND translation = ?
            """,
            (book_name, chapter, translation.lower())
        )
        row = self.cur.fetchone()
        return row["max_verse"] if row else None

    def set_cached_max_verse(self, book_name: str, chapter: int, translation: str, max_verse: int) -> None:
        """
        Cache max verse for a book, chapter, and translation.

        Args:
            book_name: Name of the book (e.g., "John")
            chapter: Chapter number
            translation: Translation identifier (e.g., "web")
            max_verse: Maximum verse number to cache
        """
        self.cur.execute(
            """
            INSERT OR REPLACE INTO book_verse_cache
            (book_name, chapter, translation, max_verse, last_updated)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (book_name, chapter, translation.lower(), max_verse)
        )
        self.conn.commit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
