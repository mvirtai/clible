"""
Tests for translation comparison statistics functionality.

This module tests the calculate_translation_differences function that analyzes
differences between two Bible translations.
"""

import pytest
from app.analytics.translation_compare import calculate_translation_differences


class TestCalculateTranslationDifferences:
    """Test translation difference calculation."""

    def test_calculate_basic_statistics(self):
        """Test that basic statistics are calculated correctly."""
        comparison_data = {
            "reference": "John 3:16",
            "translation1": {
                "verses": [
                    {"verse": 16, "text": "For God so loved the world that he gave"}
                ]
            },
            "translation2": {
                "verses": [
                    {"verse": 16, "text": "For God so loved the world that he sent"}
                ]
            }
        }
        
        stats = calculate_translation_differences(comparison_data)
        
        assert "similarity_ratio" in stats
        assert "word_count_1" in stats
        assert "word_count_2" in stats
        assert stats["word_count_1"] == 9
        assert stats["word_count_2"] == 9
        assert 0.0 <= stats["similarity_ratio"] <= 1.0

    def test_identify_unique_words(self):
        """Test that unique words are identified correctly."""
        comparison_data = {
            "reference": "John 3:16",
            "translation1": {
                "verses": [
                    {"verse": 16, "text": "love faith hope"}
                ]
            },
            "translation2": {
                "verses": [
                    {"verse": 16, "text": "love grace peace"}
                ]
            }
        }
        
        stats = calculate_translation_differences(comparison_data)
        
        assert "unique_words_1" in stats
        assert "unique_words_2" in stats
        assert "faith" in stats["unique_words_1"]
        assert "hope" in stats["unique_words_1"]
        assert "grace" in stats["unique_words_2"]
        assert "peace" in stats["unique_words_2"]
        assert "love" not in stats["unique_words_1"]
        assert "love" not in stats["unique_words_2"]

    def test_count_common_words(self):
        """Test that common words are counted correctly."""
        comparison_data = {
            "reference": "John 3:16",
            "translation1": {
                "verses": [
                    {"verse": 16, "text": "God loves the world"}
                ]
            },
            "translation2": {
                "verses": [
                    {"verse": 16, "text": "God loves all people"}
                ]
            }
        }
        
        stats = calculate_translation_differences(comparison_data)
        
        assert "common_words_count" in stats
        assert stats["common_words_count"] == 2  # "god" and "loves"
        assert "unique_count_1" in stats
        assert "unique_count_2" in stats
        assert stats["unique_count_1"] == 2  # "the" and "world"
        assert stats["unique_count_2"] == 2  # "all" and "people"

    def test_handle_multiple_verses(self):
        """Test statistics for multiple verses."""
        comparison_data = {
            "reference": "John 3:16-17",
            "translation1": {
                "verses": [
                    {"verse": 16, "text": "For God so loved the world"},
                    {"verse": 17, "text": "For God sent not his Son"}
                ]
            },
            "translation2": {
                "verses": [
                    {"verse": 16, "text": "For God so loved the world"},
                    {"verse": 17, "text": "For God did not send his Son"}
                ]
            }
        }
        
        stats = calculate_translation_differences(comparison_data)
        
        assert "verse_similarities" in stats
        assert len(stats["verse_similarities"]) == 2
        assert stats["verse_similarities"][0]["verse"] == 16
        assert stats["verse_similarities"][1]["verse"] == 17
        # First verse identical, should have high similarity
        assert stats["verse_similarities"][0]["similarity"] > 0.9
        # Second verse similar but not identical
        assert 0.7 < stats["verse_similarities"][1]["similarity"] < 1.0

    def test_handle_empty_data(self):
        """Test handling of empty comparison data."""
        empty_data = {}
        stats = calculate_translation_differences(empty_data)
        assert stats == {}
        
        no_verses = {
            "reference": "John 3:16",
            "translation1": {"verses": []},
            "translation2": {"verses": []}
        }
        stats = calculate_translation_differences(no_verses)
        assert stats == {}

    def test_case_insensitive_comparison(self):
        """Test that word comparison is case-insensitive."""
        comparison_data = {
            "reference": "John 3:16",
            "translation1": {
                "verses": [
                    {"verse": 16, "text": "GOD loves the WORLD"}
                ]
            },
            "translation2": {
                "verses": [
                    {"verse": 16, "text": "god loves the world"}
                ]
            }
        }
        
        stats = calculate_translation_differences(comparison_data)
        
        # Should be nearly identical (only difference is capitalization)
        assert stats["similarity_ratio"] > 0.9
        assert stats["unique_count_1"] == 0
        assert stats["unique_count_2"] == 0
        assert stats["common_words_count"] == 4  # god, loves, the, world

    def test_high_similarity_for_identical_text(self):
        """Test that identical texts have very high similarity."""
        comparison_data = {
            "reference": "John 3:16",
            "translation1": {
                "verses": [
                    {"verse": 16, "text": "For God so loved the world"}
                ]
            },
            "translation2": {
                "verses": [
                    {"verse": 16, "text": "For God so loved the world"}
                ]
            }
        }
        
        stats = calculate_translation_differences(comparison_data)
        
        # Identical texts should have similarity very close to 1.0
        assert stats["similarity_ratio"] > 0.99
        assert stats["unique_count_1"] == 0
        assert stats["unique_count_2"] == 0

    def test_limit_unique_words_display(self):
        """Test that unique words list is limited for display."""
        # Create data with many unique words
        many_words_1 = " ".join([f"word{i}" for i in range(50)])
        many_words_2 = " ".join([f"term{i}" for i in range(50)])
        
        comparison_data = {
            "reference": "Test",
            "translation1": {
                "verses": [{"verse": 1, "text": many_words_1}]
            },
            "translation2": {
                "verses": [{"verse": 1, "text": many_words_2}]
            }
        }
        
        stats = calculate_translation_differences(comparison_data)
        
        # Should limit to 20 unique words for display
        assert len(stats["unique_words_1"]) <= 20
        assert len(stats["unique_words_2"]) <= 20
        # But total counts should be accurate
        assert stats["unique_count_1"] == 50
        assert stats["unique_count_2"] == 50

