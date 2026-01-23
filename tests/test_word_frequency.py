import json
from pathlib import Path

import pytest

from app.analytics.word_frequency import WordFrequencyAnalyzer, DEFAULT_STOP_WORDS


class TestWordFrequencyAnalyzer:
    def test_loads_stop_words_from_custom_path(self, tmp_path: Path, caplog):
        stop_words_file = tmp_path / "stop_words.json"
        stop_words_file.write_text(json.dumps(["hello", "world"]), encoding="utf-8")

        analyzer = WordFrequencyAnalyzer(stop_words_path=stop_words_file)

        assert analyzer.stop_words == {"hello", "world"}

    def test_falls_back_to_default_when_missing(self, tmp_path: Path, caplog):
        missing_file = tmp_path / "missing.json"

        analyzer = WordFrequencyAnalyzer(stop_words_path=missing_file)

        assert analyzer.stop_words == DEFAULT_STOP_WORDS

    def test_tokenize_filters_stop_words(self, tmp_path: Path):
        stop_words_file = tmp_path / "stop_words.json"
        stop_words_file.write_text(json.dumps(["foo", "bar"]), encoding="utf-8")

        analyzer = WordFrequencyAnalyzer(stop_words_path=stop_words_file)
        tokens = analyzer.tokenize("Foo bar baz foo")

        assert tokens == ["baz"]


