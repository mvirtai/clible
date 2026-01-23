"""
Tests for API cache functionality.

Verifies that max chapters and max verses are cached in the database
to avoid unnecessary API calls and improve performance.
"""

import pytest
from pytest_mock import MockerFixture
from unittest.mock import Mock, call
import tempfile
from pathlib import Path

from app.api import calculate_max_chapter, calculate_max_verse
from app.db.queries import QueryDB


class TestCacheMaxChapter:
    """Tests for caching max chapter values"""

    def test_uses_cached_value_when_available(self, mocker: MockerFixture):
        """Test that cached max chapter is used instead of API call"""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            # Set up cache with a value
            with QueryDB(db_path) as db:
                db.set_cached_max_chapter("John", "web", 21)
            
            # Mock requests to ensure no API calls are made
            mock_get = mocker.patch('app.api.requests.get')
            mock_sleep = mocker.patch('app.api.time.sleep')
            
            # Mock QueryDB to use our temporary database
            original_querydb = QueryDB
            def mock_querydb(*args, **kwargs):
                if not args and not kwargs:
                    return original_querydb(db_path)
                return original_querydb(*args, **kwargs)
            mocker.patch('app.db.queries.QueryDB', side_effect=mock_querydb)
            
            # Call function
            result = calculate_max_chapter("John", "web")
            
            # Should return cached value
            assert result == 21
            
            # Verify no API calls were made (requests.get should not be called)
            # Note: The function still checks chapter 1 to verify book exists,
            # but we can verify it doesn't do the full search
            assert mock_get.call_count <= 1  # Only the initial chapter 1 check
            
        finally:
            # Clean up
            if db_path.exists():
                db_path.unlink()

    def test_caches_value_after_calculation(self, mocker: MockerFixture):
        """Test that calculated max chapter is cached"""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            # Mock requests
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"verses": [{"verse": 1}]}
            mock_get = mocker.patch('app.api.requests.get', return_value=mock_response)
            mock_sleep = mocker.patch('app.api.time.sleep')
            
            # Mock QueryDB to use our temporary database
            original_querydb = QueryDB
            def mock_querydb(*args, **kwargs):
                if not args and not kwargs:
                    return original_querydb(db_path)
                return original_querydb(*args, **kwargs)
            mocker.patch('app.db.queries.QueryDB', side_effect=mock_querydb)
            
            # First call - should calculate and cache
            result = calculate_max_chapter("John", "web")
            
            # Verify value was cached
            with QueryDB(db_path) as db:
                cached = db.get_cached_max_chapter("John", "web")
                assert cached == result
                assert cached is not None
            
        finally:
            # Clean up
            if db_path.exists():
                db_path.unlink()

    def test_handles_cache_failure_gracefully(self, mocker: MockerFixture):
        """Test that function works even if cache check fails"""
        # Mock QueryDB to raise an exception when imported
        def raise_on_import(*args, **kwargs):
            raise Exception("Database error")
        mocker.patch('app.db.queries.QueryDB', side_effect=raise_on_import)
        
        # Mock requests
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"verses": [{"verse": 1}]}
        mock_get = mocker.patch('app.api.requests.get', return_value=mock_response)
        mock_sleep = mocker.patch('app.api.time.sleep')
        
        # Function should still work (fall back to API)
        result = calculate_max_chapter("John", "web")
        
        # Should return a valid result
        assert result is not None
        assert result >= 1


class TestCacheMaxVerse:
    """Tests for caching max verse values"""

    def test_uses_cached_value_when_available(self, mocker: MockerFixture):
        """Test that cached max verse is used instead of API call"""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            # Set up cache with a value
            with QueryDB(db_path) as db:
                db.set_cached_max_verse("John", 3, "web", 36)
            
            # Mock requests to ensure no API calls are made
            mock_get = mocker.patch('app.api.requests.get')
            mock_sleep = mocker.patch('app.api.time.sleep')
            
            # Mock QueryDB to use our temporary database
            original_querydb = QueryDB
            def mock_querydb(*args, **kwargs):
                if not args and not kwargs:
                    return original_querydb(db_path)
                return original_querydb(*args, **kwargs)
            mocker.patch('app.db.queries.QueryDB', side_effect=mock_querydb)
            
            # Call function
            result = calculate_max_verse("John", "3", "web")
            
            # Should return cached value
            assert result == 36
            
            # Verify no API calls were made
            assert mock_get.call_count == 0
            
        finally:
            # Clean up
            if db_path.exists():
                db_path.unlink()

    def test_caches_value_after_calculation(self, mocker: MockerFixture):
        """Test that calculated max verse is cached"""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            # Mock requests
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "verses": [
                    {"verse": 1, "text": "Verse 1"},
                    {"verse": 2, "text": "Verse 2"},
                    {"verse": 3, "text": "Verse 3"}
                ]
            }
            mock_get = mocker.patch('app.api.requests.get', return_value=mock_response)
            mock_sleep = mocker.patch('app.api.time.sleep')
            
            # Mock QueryDB to use our temporary database
            original_querydb = QueryDB
            def mock_querydb(*args, **kwargs):
                if not args and not kwargs:
                    return original_querydb(db_path)
                return original_querydb(*args, **kwargs)
            mocker.patch('app.db.queries.QueryDB', side_effect=mock_querydb)
            
            # First call - should calculate and cache
            result = calculate_max_verse("John", "3", "web")
            
            # Verify value was cached
            with QueryDB(db_path) as db:
                cached = db.get_cached_max_verse("John", 3, "web")
                assert cached == result
                assert cached == 3  # Max verse from mock data
            
        finally:
            # Clean up
            if db_path.exists():
                db_path.unlink()

    def test_handles_cache_failure_gracefully(self, mocker: MockerFixture):
        """Test that function works even if cache check fails"""
        # Mock QueryDB to raise an exception when imported
        def raise_on_import(*args, **kwargs):
            raise Exception("Database error")
        mocker.patch('app.db.queries.QueryDB', side_effect=raise_on_import)
        
        # Mock requests
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "verses": [
                {"verse": 1, "text": "Verse 1"},
                {"verse": 2, "text": "Verse 2"}
            ]
        }
        mock_get = mocker.patch('app.api.requests.get', return_value=mock_response)
        mock_sleep = mocker.patch('app.api.time.sleep')
        
        # Function should still work (fall back to API)
        result = calculate_max_verse("John", "3", "web")
        
        # Should return a valid result
        assert result is not None
        assert result >= 1


class TestCacheDatabaseOperations:
    """Tests for cache database operations"""

    def test_get_cached_max_chapter_returns_none_when_not_cached(self):
        """Test that get_cached_max_chapter returns None for uncached values"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            with QueryDB(db_path) as db:
                result = db.get_cached_max_chapter("NonExistentBook", "web")
                assert result is None
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_set_and_get_cached_max_chapter(self):
        """Test setting and getting cached max chapter"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            with QueryDB(db_path) as db:
                # Set cache
                db.set_cached_max_chapter("John", "web", 21)
                
                # Get cache
                result = db.get_cached_max_chapter("John", "web")
                assert result == 21
                
                # Update cache
                db.set_cached_max_chapter("John", "web", 22)
                result = db.get_cached_max_chapter("John", "web")
                assert result == 22
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_get_cached_max_verse_returns_none_when_not_cached(self):
        """Test that get_cached_max_verse returns None for uncached values"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            with QueryDB(db_path) as db:
                result = db.get_cached_max_verse("John", 3, "web")
                assert result is None
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_set_and_get_cached_max_verse(self):
        """Test setting and getting cached max verse"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            with QueryDB(db_path) as db:
                # Set cache
                db.set_cached_max_verse("John", 3, "web", 36)
                
                # Get cache
                result = db.get_cached_max_verse("John", 3, "web")
                assert result == 36
                
                # Update cache
                db.set_cached_max_verse("John", 3, "web", 37)
                result = db.get_cached_max_verse("John", 3, "web")
                assert result == 37
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_cache_is_translation_specific(self):
        """Test that cache is specific to translation"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            with QueryDB(db_path) as db:
                # Set cache for different translations
                db.set_cached_max_chapter("John", "web", 21)
                db.set_cached_max_chapter("John", "kjv", 22)
                
                # Verify they are separate
                assert db.get_cached_max_chapter("John", "web") == 21
                assert db.get_cached_max_chapter("John", "kjv") == 22
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_cache_is_book_specific(self):
        """Test that cache is specific to book"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            with QueryDB(db_path) as db:
                # Set cache for different books
                db.set_cached_max_chapter("John", "web", 21)
                db.set_cached_max_chapter("Matthew", "web", 28)
                
                # Verify they are separate
                assert db.get_cached_max_chapter("John", "web") == 21
                assert db.get_cached_max_chapter("Matthew", "web") == 28
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_cache_is_chapter_specific_for_verses(self):
        """Test that verse cache is specific to chapter"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            with QueryDB(db_path) as db:
                # Set cache for different chapters
                db.set_cached_max_verse("John", 3, "web", 36)
                db.set_cached_max_verse("John", 4, "web", 54)
                
                # Verify they are separate
                assert db.get_cached_max_verse("John", 3, "web") == 36
                assert db.get_cached_max_verse("John", 4, "web") == 54
        finally:
            if db_path.exists():
                db_path.unlink()

