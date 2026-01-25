"""
Analysis tracking and history management.

Automatically saves analysis results to database for later retrieval,
comparison, and historical analysis.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

from loguru import logger

from app.db.queries import QueryDB


class AnalysisTracker:
    """
    Tracks and stores analysis results for historical reference.

    Automatically saves:
      - Analysis metadata
      - Results (word frequencies, phrases, stats)
      - Visualization paths
    """

    def __init__(self, user_id: str = None, session_id: str = None, db_path=None):
        self.user_id = user_id
        self.session_id = session_id
        self.db_path = db_path

    def _get_db(self):
        """
        Get QueryDB instance with appropriate db_path.

        If db_path is None, uses the default DB_PATH from QueryDB.
        If db_path is set (e.g. for testing), uses that path.
        """
        if self.db_path is None:
            return QueryDB()
        return QueryDB(self.db_path)

    def save_word_frequency_analysis(
        self,
        word_freq: list[tuple[str, int]],
        vocab_info: dict,
        scope_type: str,
        scope_details: dict,
        verse_count: int,
        chart_paths: dict = None
    ) -> str:
        """
        Save word frequency analysis to database.

        Args:
            word_freq: List of (word, count) tuples
            vocab_info: Dictionary with vocabulary statistics
            scope_type: 'query', 'session', 'book', or 'multi_query'
            scope_details: Dict describing the scope
            verse_count: Number of verses analyzed
            chart_paths: Optional dict with 'word_freq' and 'vocab_info' paths
        """
        analysis_id = uuid.uuid4().hex[:8]

        with self._get_db() as db:
            user_name = "Unknown"
            if self.user_id:
                user = db.get_user_by_id(self.user_id)
                user_name = user["name"] if user else "Unknown"

            db.cur.execute("""
                INSERT INTO analysis_history (
                    id, user_id, session_id, user_name, analysis_type,
                    scope_type, scope_details, verse_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_id,
                self.user_id,
                self.session_id,
                user_name,
                "word_frequency",
                scope_type,
                json.dumps(scope_details),
                verse_count
            ))

            word_freq_id = uuid.uuid4().hex[:8]
            db.cur.execute("""
                INSERT INTO analysis_results (
                    id, analysis_id, result_type, result_data, chart_path
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                word_freq_id,
                analysis_id,
                "word_freq",
                json.dumps(word_freq),
                chart_paths.get('word_freq') if chart_paths else None
            ))

            vocab_stats_id = uuid.uuid4().hex[:8]
            db.cur.execute("""
                INSERT INTO analysis_results (
                    id, analysis_id, result_type, result_data, chart_path
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                vocab_stats_id,
                analysis_id,
                'vocab_stats',
                json.dumps(vocab_info),
                chart_paths.get('vocab_stats') if chart_paths else None
            ))

            db.conn.commit()

        logger.info(f"Saved word frequency analysis: {analysis_id}")
        return analysis_id

    def save_phrase_analysis(
        self,
        bigrams: list[tuple[str, int]],
        trigrams: list[tuple[str, int]],
        scope_type: str,
        scope_details: dict,
        verse_count: int,
        chart_paths: dict = None
    ) -> str:
        """
        Save phrase analysis (bigrams and trigrams) to database.

        Args:
            bigrams: List of (bigram_phrase, count) tuples
            trigrams: List of (trigram_phrase, count) tuples
            scope_type: 'query', 'session', 'book', or 'multi_query'
            scope_details: Dict describing the scope
            verse_count: Number of verses analyzed
            chart_paths: Optional dict with 'bigram' and 'trigram' paths

        Returns:
            analysis_id: Unique ID for this analysis
        """
        analysis_id = uuid.uuid4().hex[:8]

        with self._get_db() as db:
            user_name = "Unknown"
            if self.user_id:
                user = db.get_user_by_id(self.user_id)
                user_name = user["name"] if user else "Unknown"

            db.cur.execute("""
                INSERT INTO analysis_history (
                    id, user_id, session_id, user_name, analysis_type,
                    scope_type, scope_details, verse_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_id,
                self.user_id,
                self.session_id,
                user_name,
                "phrase_analysis",
                scope_type,
                json.dumps(scope_details),
                verse_count
            ))

            bigram_id = uuid.uuid4().hex[:8]
            db.cur.execute("""
                INSERT INTO analysis_results (
                    id, analysis_id, result_type, result_data, chart_path
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                bigram_id,
                analysis_id,
                "bigram",
                json.dumps(bigrams),
                chart_paths.get('bigram') if chart_paths else None
            ))

            trigram_id = uuid.uuid4().hex[:8]
            db.cur.execute("""
                INSERT INTO analysis_results (
                    id, analysis_id, result_type, result_data, chart_path
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                trigram_id,
                analysis_id,
                "trigram",
                json.dumps(trigrams),
                chart_paths.get('trigram') if chart_paths else None
            ))

            db.conn.commit()

        logger.info(f"Saved phrase analysis: {analysis_id}")
        return analysis_id

    def save_translation_comparison(
        self,
        comparison_data: dict,
        scope_type: str,
        scope_details: dict,
        verse_count: int
    ) -> str:
        """
        Save translation comparison analysis to database.

        Args:
            comparison_data: Dictionary containing translation comparison data with:
                - "reference": Verse reference string
                - "translation1": Dict with first translation data (verses, translation_name, translation_id)
                - "translation2": Dict with second translation data (verses, translation_name, translation_id)
            scope_type: 'translation' or other scope type
            scope_details: Dict describing the scope (e.g., {"translation1": "web", "translation2": "kjv"})
            verse_count: Number of verses compared

        Returns:
            analysis_id: Unique ID for this analysis
        """
        analysis_id = uuid.uuid4().hex[:8]

        with self._get_db() as db:
            user_name = "Unknown"
            if self.user_id:
                user = db.get_user_by_id(self.user_id)
                user_name = user["name"] if user else "Unknown"

            db.cur.execute("""
                INSERT INTO analysis_history (
                    id, user_id, session_id, user_name, analysis_type,
                    scope_type, scope_details, verse_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_id,
                self.user_id,
                self.session_id,
                user_name,
                "translation_comparison",
                scope_type,
                json.dumps(scope_details),
                verse_count
            ))

            comparison_id = uuid.uuid4().hex[:8]
            db.cur.execute("""
                INSERT INTO analysis_results (
                    id, analysis_id, result_type, result_data, chart_path
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                comparison_id,
                analysis_id,
                "translation_comparison",
                json.dumps(comparison_data),
                None
            ))

            db.conn.commit()

        logger.info(f"Saved translation comparison: {analysis_id}")
        return analysis_id

    def get_analysis_history(
        self,
        limit: int = 10,
        analysis_type: str = None,
        scope_type: str = None,
        session_id: str = None
    ) -> list[dict]:
        """
        Get analysis history with optional filtering.

        Args:
            limit: Max number of results to return
            analysis_type: Filter by analysis type ('word_frequency', 'phrase_analysis')
            scope_type: Filter by scope type ('query', 'session', 'book', 'multi_query')
            session_id: Filter by session ID (None = all sessions)

        Returns:
            List of analysis metadata dictionaries, ordered by most recent first
        """
        with self._get_db() as db:
            query = "SELECT * FROM analysis_history WHERE 1=1"
            params = []

            if self.user_id:
                query += " AND user_id = ?"
                params.append(self.user_id)

            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)

            if analysis_type:
                query += " AND analysis_type = ?"
                params.append(analysis_type)

            if scope_type:
                query += " AND scope_type = ?"
                params.append(scope_type)

            query += " ORDER BY created_at DESC, ROWID DESC LIMIT ?"
            params.append(limit)

            db.cur.execute(query, tuple(params))
            rows = db.cur.fetchall()

            return [dict(row) for row in rows]

    def get_analysis_results(self, analysis_id: str) -> dict | None:
        """
        Get complete analysis with metadata and all results.

        Args:
            analysis_id: Unique ID of the analysis to retrieve

        Returns:
            Dictionary containing:
            - All analysis_history fields (id, analysis_type, scope_type, etc.)
            - 'results': dict of {result_type: deserialized_data}
            - 'chart_paths': dict of {result_type: path}
            Returns None if analysis not found.
        """
        with self._get_db() as db:
            db.cur.execute("""
                SELECT
                    h.*,
                    r.result_type,
                    r.result_data,
                    r.chart_path
                FROM analysis_history h
                LEFT JOIN analysis_results r ON h.id = r.analysis_id
                WHERE h.id = ?
            """, (analysis_id,))

            rows = db.cur.fetchall()

            if not rows:
                return None

            first_row = rows[0]
            analysis = {
                "id": first_row["id"],
                "user_id": first_row["user_id"],
                "session_id": first_row["session_id"],
                "analysis_type": first_row["analysis_type"],
                "scope_type": first_row["scope_type"],
                "scope_details": json.loads(first_row["scope_details"]) if first_row["scope_details"] else {},
                "verse_count": first_row["verse_count"],
                "created_at": first_row["created_at"],
                "results": {},
                "chart_paths": {}
            }

            for row in rows:
                if row["result_type"]:
                    result_data = json.loads(row["result_data"])
                    analysis["results"][row["result_type"]] = result_data

                    if row["chart_path"]:
                        analysis["chart_paths"][row["result_type"]] = row["chart_path"]

            return analysis
