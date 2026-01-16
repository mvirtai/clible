"""
Tests for AnalyticsVisualizer class.

Tests cover:
- Export directory creation
- Terminal display (smoke tests)
- PNG file exports
- HTML file exports
- Error handling for empty data
- File path generation
"""

import pytest
from pathlib import Path
import tempfile
import json

from app.analytics.visualizations import AnalyticsVisualizer


@pytest.fixture
def temp_export_dir():
    """Create temporary export directory."""
    temp_dir = tempfile.mkdtemp()
    export_path = Path(temp_dir) / "test_charts"
    yield export_path
    
    # Cleanup
    if export_path.exists():
        for file in export_path.rglob("*"):
            if file.is_file():
                file.unlink()


@pytest.fixture
def sample_word_freq():
    """Sample word frequency data."""
    return [
        ("jesus", 120),
        ("lord", 85),
        ("god", 65),
        ("love", 45),
        ("faith", 30)
    ]


@pytest.fixture
def sample_vocab_info():
    """Sample vocabulary statistics."""
    return {
        "total_tokens": 1500,
        "vocabulary_size": 450,
        "type_token_ratio": 0.3
    }



class TestInitialization:
    """Test AnalyticsVisualizer initialization"""

    def test_creates_export_directory(self, temp_export_dir):
        """Test that export directory is created on init"""
        viz = AnalyticsVisualizer(export_dir=temp_export_dir)
        assert temp_export_dir.exists()
        assert temp_export_dir.is_dir()

    def test_uses_default_dir_if_none_provided(self):
        """Test that default export directory is used if none provided"""
        viz = AnalyticsVisualizer()
        assert viz.export_dir == Path("data/charts")


class TestPlotWordFrequency:
    """Test word frequency plotting."""
    
    def test_terminal_display_doesnt_crash(self, sample_word_freq, temp_export_dir):
        """Test that terminal display executes without error."""
        viz = AnalyticsVisualizer(export_dir=temp_export_dir)
        
        # Should not raise exception
        result = viz.plot_word_frequency(
            word_freq=sample_word_freq,
            display="terminal"
        )
        
        assert result is None  # No file created
    
    def test_png_export_creates_file(self, sample_word_freq, temp_export_dir):
        """Test that PNG export creates file."""
        viz = AnalyticsVisualizer(export_dir=temp_export_dir)
        
        result = viz.plot_word_frequency(
            word_freq=sample_word_freq,
            display="export",
            export_format="png"
        )
        
        assert result is not None
        assert result.exists()
        assert result.suffix == ".png"
        assert "word_freq" in result.name
    
    def test_html_export_creates_file(self, sample_word_freq, temp_export_dir):
        """Test that HTML export creates file."""
        viz = AnalyticsVisualizer(export_dir=temp_export_dir)
        
        result = viz.plot_word_frequency(
            word_freq=sample_word_freq,
            display="export",
            export_format="html"
        )
        
        assert result is not None
        assert result.exists()
        assert result.suffix == ".html"
    
    def test_both_mode_creates_file(self, sample_word_freq, temp_export_dir):
        """Test that 'both' mode displays and exports."""
        viz = AnalyticsVisualizer(export_dir=temp_export_dir)
        
        result = viz.plot_word_frequency(
            word_freq=sample_word_freq,
            display="both",
            export_format="png"
        )
        
        assert result is not None
        assert result.exists()
    
    def test_handles_empty_data(self, temp_export_dir):
        """Test handling of empty word frequency list."""
        viz = AnalyticsVisualizer(export_dir=temp_export_dir)
        
        result = viz.plot_word_frequency(
            word_freq=[],
            display="export"
        )
        
        assert result is None  # No file created
    
    def test_respects_top_n_parameter(self, temp_export_dir):
        """Test that top_n limits displayed words."""
        viz = AnalyticsVisualizer(export_dir=temp_export_dir)
        
        large_freq = [(f"word_{i}", 100-i) for i in range(100)]
        
        result = viz.plot_word_frequency(
            word_freq=large_freq,
            display="export",
            top_n=10
        )
        
        # Would need to parse PNG to verify, so just check file created
        assert result is not None
        assert result.exists()


class TestPlotPhraseFrequency:
    """Test phrase frequency plotting."""
    
    def test_plots_bigrams_and_trigrams(self, temp_export_dir):
        """Test plotting both bigrams and trigrams separately."""
        viz = AnalyticsVisualizer(export_dir=temp_export_dir)
        
        bigrams = [("love god", 45), ("holy spirit", 32)]
        trigrams = [("in the beginning", 15), ("son of god", 12)]
        
        # Plot bigrams (separate call)
        bigram_result = viz.plot_phrase_frequency(
            phrases=bigrams,
            title="Top Bigrams",
            display="export",
            export_format="png"
        )
        
        # Plot trigrams (separate call)
        trigram_result = viz.plot_phrase_frequency(
            phrases=trigrams,
            title="Top Trigrams",
            display="export",
            export_format="png"
        )
        
        # Both files should be created
        assert bigram_result is not None
        assert bigram_result.exists()
        assert trigram_result is not None
        assert trigram_result.exists()


class TestPlotVocabularyStats:
    """Test vocabulary statistics plotting."""
    
    def test_plots_vocab_stats(self, sample_vocab_info, temp_export_dir):
        """Test plotting vocabulary statistics."""
        viz = AnalyticsVisualizer(export_dir=temp_export_dir)
        
        result = viz.plot_vocabulary_stats(
            vocab_info=sample_vocab_info,
            display="export",
            export_format="png"
        )
        
        assert result is not None
        assert result.exists()
        assert "vocab_stats" in result.name