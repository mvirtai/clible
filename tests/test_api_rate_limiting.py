"""
Tests for API rate limiting functionality.

Verifies that appropriate delays are added between API calls to prevent
429 (Too Many Requests) errors from the bible-api.com API.
"""

import pytest
from pytest_mock import MockerFixture
from unittest.mock import Mock, call
import time

from app.api import (
    calculate_max_chapter,
    calculate_max_verse,
    fetch_by_reference,
    fetch_book_list
)
from app.analytics.translation_compare import fetch_verse_comparison


class TestCalculateMaxChapterRateLimiting:
    """Tests for rate limiting in calculate_max_chapter function"""

    def test_adds_delay_between_test_chapters(self, mocker: MockerFixture):
        """Test that delays are added between chapter discovery calls"""
        mock_sleep = mocker.patch('app.api.time.sleep')
        mock_get = mocker.patch('app.api.requests.get')
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"verses": [{"verse": 1}]}
        mock_get.return_value = mock_response
        
        # Call function
        result = calculate_max_chapter("John", "web")
        
        # Verify sleep was called (should be called for each test chapter after first)
        # test_chapters = [50, 30, 20, 10], so 3 sleeps expected (for 30, 20, 10)
        assert mock_sleep.call_count >= 3
        # Verify all sleeps are 1 second
        assert all(call_args == call(1) for call_args in mock_sleep.call_args_list)

    def test_adds_delay_during_upward_search(self, mocker: MockerFixture):
        """Test that delays are added during upward chapter search"""
        # Mock cache to return None (no cached value)
        mock_db_context = Mock()
        mock_db_context.get_cached_max_chapter.return_value = None
        mock_db_instance = Mock()
        mock_db_instance.__enter__ = Mock(return_value=mock_db_context)
        mock_db_instance.__exit__ = Mock(return_value=None)
        mocker.patch('app.db.queries.QueryDB', return_value=mock_db_instance)
        
        mock_sleep = mocker.patch('app.api.time.sleep')
        mock_get = mocker.patch('app.api.requests.get')
        
        # Mock responses: chapter 1 exists, chapter 10 exists, then chapters 11-13 exist
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"verses": [{"verse": 1}]}
        
        mock_response_404 = Mock()
        mock_response_404.status_code = 404
        
        def side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if '10' in url:
                return mock_response_200
            elif any(str(i) in url for i in [11, 12, 13]):
                return mock_response_200
            elif '14' in url:
                return mock_response_404
            return mock_response_200
        
        mock_get.side_effect = side_effect
        
        # Call function
        result = calculate_max_chapter("John", "web")
        
        # Should have multiple sleep calls (for test chapters + upward search)
        assert mock_sleep.call_count > 0
        # All sleeps should be 1 second
        assert all(call_args == call(1) for call_args in mock_sleep.call_args_list)


class TestCalculateMaxVerseRateLimiting:
    """Tests for rate limiting in calculate_max_verse function"""

    def test_adds_delay_before_api_call(self, mocker: MockerFixture):
        """Test that delay is added before fetching chapter for verse calculation"""
        mock_sleep = mocker.patch('app.api.time.sleep')
        mock_get = mocker.patch('app.api.requests.get')
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "verses": [
                {"verse": 1, "text": "Verse 1"},
                {"verse": 2, "text": "Verse 2"},
                {"verse": 3, "text": "Verse 3"}
            ]
        }
        mock_get.return_value = mock_response
        
        # Call function
        result = calculate_max_verse("John", "3", "web")
        
        # Verify sleep was called once before the API call
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_once_with(1)


class TestFetchByReferenceRateLimiting:
    """Tests for rate limiting in fetch_by_reference function"""

    def test_adds_delay_before_main_api_call(self, mocker: MockerFixture):
        """Test that delay is added before main API call"""
        mock_sleep = mocker.patch('app.api.time.sleep')
        mock_get = mocker.patch('app.api.requests.get')
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "reference": "John 3:16",
            "verses": [{"verse": 16, "text": "For God so loved..."}]
        }
        mock_get.return_value = mock_response
        
        # Call function
        result = fetch_by_reference("John", "3", "16", use_mock=False)
        
        # Verify sleep was called at least once
        assert mock_sleep.call_count >= 1
        # Verify at least one call is 1 second
        assert any(call_args == call(1) for call_args in mock_sleep.call_args_list)

    def test_adds_delay_after_max_chapter_calculation(self, mocker: MockerFixture):
        """Test that delay is added after calculating max chapter"""
        mock_sleep = mocker.patch('app.api.time.sleep')
        mock_get = mocker.patch('app.api.requests.get')
        
        # Mock calculate_max_chapter to return a value
        mock_calc = mocker.patch('app.api.calculate_max_chapter', return_value=21)
        
        # Mock successful response for final fetch
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "reference": "John 21",
            "verses": []
        }
        mock_get.return_value = mock_response
        
        # Call function with chapter='all'
        result = fetch_by_reference("John", "all", None, use_mock=False)
        
        # Should have sleep calls (one after max_chapter calculation, one before final fetch)
        assert mock_sleep.call_count >= 1


class TestFetchBookListRateLimiting:
    """Tests for rate limiting in fetch_book_list function"""

    def test_adds_delay_before_api_call(self, mocker: MockerFixture):
        """Test that delay is added before fetching book list"""
        mock_sleep = mocker.patch('app.api.time.sleep')
        mock_get = mocker.patch('app.api.requests.get')
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"books": [{"name": "Genesis"}]}
        mock_get.return_value = mock_response
        
        # Call function
        result = fetch_book_list()
        
        # Verify sleep was called once
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_once_with(1)


class TestTranslationCompareRateLimiting:
    """Tests for rate limiting in translation comparison"""

    def test_adds_delay_between_translation_fetches(self, mocker: MockerFixture):
        """Test that delay is added between fetching two translations"""
        mock_sleep = mocker.patch('app.analytics.translation_compare.time.sleep')
        mock_fetch = mocker.patch('app.analytics.translation_compare.fetch_by_reference')
        
        # Mock successful responses for both translations
        mock_data_1 = {
            "reference": "John 3:16",
            "verses": [{"verse": 16, "text": "For God so loved..."}],
            "translation_name": "World English Bible",
            "translation_id": "web"
        }
        mock_data_2 = {
            "reference": "John 3:16",
            "verses": [{"verse": 16, "text": "For God so loved the world..."}],
            "translation_name": "King James Version",
            "translation_id": "kjv"
        }
        mock_fetch.side_effect = [mock_data_1, mock_data_2]
        
        # Call function
        result = fetch_verse_comparison("John", "3", "16", "web", "kjv")
        
        # Verify sleep was called once between the two fetches
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_once_with(1)
        
        # Verify fetch_by_reference was called twice
        assert mock_fetch.call_count == 2

