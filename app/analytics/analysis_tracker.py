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
      - Visualzation paths
    """

    def __init__(self, user_id: str = None, session_id: str = None):
        self.user_id = user_id
        self.session_id = session_id
    

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
                # TODO: Implement this
        # 1. Create analysis_id
        # 2. Insert into analysis_history
        # 3. Insert word_freq results into analysis_results
        # 4. Insert vocab_stats results into analysis_results
        # 5. Return analysis_id

        # 1. Generate ID
        analysis_id = uuid.uuid4().hex[:8]

        with QueryDB() as db:
            # 2. Insert into analysis_history
            db.cur.execute("""
                INSERT INTO analysis_history (
                    id, user_id, session_id, analysis_type,
                    scope_type, scope_details, verse_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_id,
                self.user_id,
                self.session_id,
                "word_freq",
                scope_type,
                json.dumps(scope_details),
                verse_count
            ))

            # 3. Insert word_freq results
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

            # 4. Insert vocab_stats results
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

            # Commit all changes
            db.conn.commit()
        
        # 5. Log and return
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
        """Save phrase analysis to database."""
        # TODO: Similar structure to word_frequency
        pass
    
    def get_analysis_history(
        self,
        limit: int = 10,
        analysis_type: str = None,
        scope_type: str = None
    ) -> list[dict]:
        """
        Get analysis history.
        
        Args:
            limit: Max number of results
            analysis_type: Filter by type
            scope_type: Filter by scope
            
        Returns:
            List of analysis metadata
        """
        # TODO: Query analysis_history with filters
        pass
    
    def get_analysis_results(self, analysis_id: str) -> dict:
        """
        Get full results for a specific analysis.
        
        Returns:
            Dict with all results and metadata
        """
        # TODO: Join analysis_history and analysis_results
        pass
    
    def compare_analyses(self, analysis_id1: str, analysis_id2: str) -> dict:
        """
        Compare two analyses.
        
        Returns:
            Dict with comparison metrics
        """
        # TODO: Compare word frequencies, find differences
        pass

