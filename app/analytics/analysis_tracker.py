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

    def __init__(self, user_id: str = None, session_id: str = None, db_path=None):
        self.user_id = user_id
        self.session_id = session_id
        self.db_path = db_path
    

    def _get_db(self):
        """
        Get QueryDB instance with appropriate db_path.

        if db_path is None, uses the default DB_PATH from QueryDB.
        If db_path is set (e.g. for testing), uses that path,
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
  
        # 1. Generate ID
        analysis_id = uuid.uuid4().hex[:8]

        with self._get_db() as db:

            # 2. Get user name if user_id is available
            user_name = None
            if self.user_id:
                user = db.get_user_by_id(self.user_id)
                user_name = user["name"] if user else None
            
            # 3. Insert into analysis history
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

            # 4. Insert word_freq results
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

            # 5. Insert vocab_stats results
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
        
        # 6. Log and return
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
        # Generate unique analysis ID
        analysis_id = uuid.uuid4().hex[:8]

        with self._get_db() as db:
            # Get user name if user_id is available
            user_name = None
            if self.user_id:
                user = db.get_user_by_id(self.user_id)
                user_name = user["name"] if user else None

            # Insert metadata into analysis_history
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
            
            # Insert bigram results
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
            
            # Insert trigram results
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
            
            # Commit all changes
            db.conn.commit()
        
        logger.info(f"Saved phrase analysis: {analysis_id}")
        return analysis_id
    
    def get_analysis_history(
        self,
        limit: int = 10,
        analysis_type: str = None,
        scope_type: str = None
    ) -> list[dict]:
        """
        Get analysis history with optional filtering.
        
        Args:
            limit: Max number of results to return
            analysis_type: Filter by analysis type ('word_frequency', 'phrase_analysis')
            scope_type: Filter by scope type ('query', 'session', 'book', 'multi_query')
            
        Returns:
            List of analysis metadata dictionaries, ordered by most recent first
        """
        with self._get_db() as db:
            # Build dynamic query with optional filters
            query = "SELECT * FROM analysis_history WHERE 1=1"
            params = []
            
            # Filter by user if user_id is set
            if self.user_id:
                query += " AND user_id = ?"
                params.append(self.user_id)
            
            # Filter by analysis_type if provided
            if analysis_type:
                query += " AND analysis_type = ?"
                params.append(analysis_type)
            
            # Filter by scope_type if provided
            if scope_type:
                query += " AND scope_type = ?"
                params.append(scope_type)
            
            # Order by most recent first (with ROWID as tiebreaker for same timestamp)
            query += " ORDER BY created_at DESC, ROWID DESC LIMIT ?"
            params.append(limit)
            
            db.cur.execute(query, tuple(params))
            rows = db.cur.fetchall()
            
            # Convert Row objects to dictionaries
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
            # JOIN analysis_history and analysis_results to get complete data
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
            
            # If no rows found, analysis doesn't exist
            if not rows:
                return None
            
            # Build analysis dictionary from first row (metadata)
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
            
            # Process all result rows and deserialize JSON data
            for row in rows:
                if row["result_type"]:  # Result exists (LEFT JOIN might have NULLs)
                    # Deserialize JSON string to Python object
                    result_data = json.loads(row["result_data"])
                    analysis["results"][row["result_type"]] = result_data
                    
                    # Add chart path if it exists
                    if row["chart_path"]:
                        analysis["chart_paths"][row["result_type"]] = row["chart_path"]
            
            return analysis
    
    def compare_analyses(self, analysis_id1: str, analysis_id2: str) -> dict | None:
        """
        Compare two word frequency analyses to find similarities and differences.
        
        Args:
            analysis_id1: ID of first analysis
            analysis_id2: ID of second analysis
            
        Returns:
            Dictionary containing:
            - 'analysis_1': Metadata of first analysis
            - 'analysis_2': Metadata of second analysis
            - 'common_words': Words present in both (word, count1, count2)
            - 'unique_to_first': Words only in first analysis
            - 'unique_to_second': Words only in second analysis
            - 'frequency_changes': Common words with count differences (word, count1, count2, diff)
            Returns None if either analysis not found.
        """
        # Retrieve both analyses
        analysis_1 = self.get_analysis_results(analysis_id1)
        analysis_2 = self.get_analysis_results(analysis_id2)
        
        # Verify both exist
        if not analysis_1 or not analysis_2:
            return None
        
        # Get word frequency data and convert to dictionaries for easier comparison
        # Note: word_freq is stored as list of [word, count] pairs
        words_1_list = analysis_1["results"].get("word_freq", [])
        words_2_list = analysis_2["results"].get("word_freq", [])
        
        # Convert lists to dictionaries: {"word": count}
        words_1 = dict(words_1_list)
        words_2 = dict(words_2_list)
        
        # Find common words (set intersection)
        common_keys = set(words_1.keys()) & set(words_2.keys())
        common_words = [(word, words_1[word], words_2[word]) for word in common_keys]
        
        # Find words unique to each analysis (set difference)
        unique_1_keys = set(words_1.keys()) - set(words_2.keys())
        unique_to_first = [(word, words_1[word]) for word in unique_1_keys]
        
        unique_2_keys = set(words_2.keys()) - set(words_1.keys())
        unique_to_second = [(word, words_2[word]) for word in unique_2_keys]
        
        # Calculate frequency changes for common words
        frequency_changes = []
        for word in common_keys:
            count1 = words_1[word]
            count2 = words_2[word]
            diff = count2 - count1
            frequency_changes.append((word, count1, count2, diff))
        
        # Sort frequency changes by absolute difference (largest changes first)
        frequency_changes.sort(key=lambda x: abs(x[3]), reverse=True)
        
        # Build comparison result
        return {
            "analysis_1": {
                "id": analysis_1["id"],
                "analysis_type": analysis_1["analysis_type"],
                "scope_type": analysis_1["scope_type"],
                "scope_details": analysis_1["scope_details"],
                "verse_count": analysis_1["verse_count"],
                "created_at": analysis_1["created_at"]
            },
            "analysis_2": {
                "id": analysis_2["id"],
                "analysis_type": analysis_2["analysis_type"],
                "scope_type": analysis_2["scope_type"],
                "scope_details": analysis_2["scope_details"],
                "verse_count": analysis_2["verse_count"],
                "created_at": analysis_2["created_at"]
            },
            "common_words": common_words,
            "unique_to_first": unique_to_first,
            "unique_to_second": unique_to_second,
            "frequency_changes": frequency_changes
        }

