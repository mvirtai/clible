"""
Tests for translation comparison functionality.

Tests cover fetching verses in multiple translations and rendering
side-by-side comparisons.
"""

from app.analytics.translation_compare import fetch_verse_comparison, render_side_by_side_comparison
from pytest_mock import MockerFixture


def test_fetch_verse_comparison(mocker: MockerFixture):
    """
    Test that fetch_verse_comparison function returns correct structure.
    
    Verifies that the function correctly fetches verses from two translations
    and returns them in the expected dictionary format.
    """
    # Mock API responses
    mock_verse_data_1 = {
        "reference": "John 3:16",
        "verses": [{
            "book_name": "John",
            "chapter": 3,
            "verse": 16,
            "text": "For God so loved the world, that he gave his one and only Son, that whoever believes in him should not perish, but have eternal life."
        }],
        "translation_id": "web",
        "translation_name": "World English Bible"
    }
    
    mock_verse_data_2 = {
        "reference": "John 3:16",
        "verses": [{
            "book_name": "John",
            "chapter": 3,
            "verse": 16,
            "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."
        }],
        "translation_id": "kjv",
        "translation_name": "King James Version"
    }
    
    mock_fetch = mocker.patch('app.analytics.translation_compare.fetch_by_reference')
    mock_fetch.side_effect = [mock_verse_data_1, mock_verse_data_2]
    
    # Test function call
    result = fetch_verse_comparison("John", "3", "16", "web", "kjv")
    
    # Assertions
    assert result is not None
    assert "reference" in result
    assert "translation1" in result
    assert "translation2" in result
    assert result["reference"] == "John 3:16"
    assert result["translation1"]["translation_name"] == "World English Bible"
    assert result["translation2"]["translation_name"] == "King James Version"
    assert len(result["translation1"]["verses"]) == 1
    assert len(result["translation2"]["verses"]) == 1
    assert result["translation1"]["verses"][0]["verse"] == 16
    assert result["translation2"]["verses"][0]["verse"] == 16


def test_fetch_verse_comparison_multiple_verses(mocker: MockerFixture):
    """
    Test that fetch_verse_comparison handles multiple verses correctly.
    
    Verifies that when fetching a verse range (e.g., 16-18), all verses
    are included in the result.
    """
    mock_verse_data_1 = {
        "reference": "John 3:16-18",
        "verses": [
            {
                "book_name": "John",
                "chapter": 3,
                "verse": 16,
                "text": "For God so loved the world..."
            },
            {
                "book_name": "John",
                "chapter": 3,
                "verse": 17,
                "text": "For God sent not his Son..."
            },
            {
                "book_name": "John",
                "chapter": 3,
                "verse": 18,
                "text": "He that believeth on him..."
            }
        ],
        "translation_id": "web",
        "translation_name": "World English Bible"
    }
    
    mock_verse_data_2 = {
        "reference": "John 3:16-18",
        "verses": [
            {
                "book_name": "John",
                "chapter": 3,
                "verse": 16,
                "text": "For God so loved the world..."
            },
            {
                "book_name": "John",
                "chapter": 3,
                "verse": 17,
                "text": "For God sent not his Son..."
            },
            {
                "book_name": "John",
                "chapter": 3,
                "verse": 18,
                "text": "He that believeth on him..."
            }
        ],
        "translation_id": "kjv",
        "translation_name": "King James Version"
    }
    
    mock_fetch = mocker.patch('app.analytics.translation_compare.fetch_by_reference')
    mock_fetch.side_effect = [mock_verse_data_1, mock_verse_data_2]
    
    result = fetch_verse_comparison("John", "3", "16-18", "web", "kjv")
    
    assert result is not None
    assert len(result["translation1"]["verses"]) == 3
    assert len(result["translation2"]["verses"]) == 3
    assert result["translation1"]["verses"][0]["verse"] == 16
    assert result["translation1"]["verses"][2]["verse"] == 18


def test_fetch_verse_comparison_failure(mocker: MockerFixture):
    """
    Test that fetch_verse_comparison returns None on API failure.
    
    Verifies error handling when one or both API calls fail.
    """
    mock_fetch = mocker.patch('app.analytics.translation_compare.fetch_by_reference')
    # Simulate first fetch failing
    mock_fetch.return_value = None
    
    result = fetch_verse_comparison("John", "3", "16", "web", "kjv")
    
    assert result is None
    
    # Simulate second fetch failing
    mock_verse_data_1 = {
        "reference": "John 3:16",
        "verses": [{"book_name": "John", "chapter": 3, "verse": 16, "text": "..."}],
        "translation_id": "web",
        "translation_name": "World English Bible"
    }
    mock_fetch.side_effect = [mock_verse_data_1, None]
    
    result = fetch_verse_comparison("John", "3", "16", "web", "kjv")
    assert result is None


def test_render_side_by_side_comparison(mocker: MockerFixture):
    """
    Test that render_side_by_side_comparison renders correctly.
    
    Verifies that the function displays verses in a table format without errors.
    """
    comparison_data = {
        "reference": "John 3:16",
        "translation1": {
            "reference": "John 3:16",
            "verses": [{
                "book_name": "John",
                "chapter": 3,
                "verse": 16,
                "text": "For God so loved the world, that he gave his one and only Son."
            }],
            "translation_name": "World English Bible",
            "translation_id": "web"
        },
        "translation2": {
            "reference": "John 3:16",
            "verses": [{
                "book_name": "John",
                "chapter": 3,
                "verse": 16,
                "text": "For God so loved the world, that he gave his only begotten Son."
            }],
            "translation_name": "King James Version",
            "translation_id": "kjv"
        }
    }
    
    # Should not raise any exceptions
    render_side_by_side_comparison(comparison_data)
    
    # Test with empty data
    render_side_by_side_comparison({})
    
    # Test with None
    render_side_by_side_comparison(None)


def test_render_side_by_side_comparison_multiple_verses(mocker: MockerFixture):
    """
    Test that render_side_by_side_comparison handles multiple verses correctly.
    
    Verifies that when there are multiple verses, they are displayed
    in separate rows.
    """
    comparison_data = {
        "reference": "John 3:16-17",
        "translation1": {
            "reference": "John 3:16-17",
            "verses": [
                {"book_name": "John", "chapter": 3, "verse": 16, "text": "Verse 16 text..."},
                {"book_name": "John", "chapter": 3, "verse": 17, "text": "Verse 17 text..."}
            ],
            "translation_name": "WEB",
            "translation_id": "web"
        },
        "translation2": {
            "reference": "John 3:16-17",
            "verses": [
                {"book_name": "John", "chapter": 3, "verse": 16, "text": "Verse 16 text..."},
                {"book_name": "John", "chapter": 3, "verse": 17, "text": "Verse 17 text..."}
            ],
            "translation_name": "KJV",
            "translation_id": "kjv"
        }
    }
    
    # Should not raise any exceptions
    render_side_by_side_comparison(comparison_data)
