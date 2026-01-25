"""
Phrase analysis (bigrams, trigrams) for clible.

Finds common word pairs and three-word phrases in saved verses.
"""

from collections import Counter

from loguru import logger

from app.analytics.word_frequency import WordFrequencyAnalyzer
from app.ui import console, format_bigrams, format_trigrams, spacing_after_output


class PhraseAnalyzer:
    """
    Analyzes phrases and n-grams in biblical verses.

    Provides methods to find most common word pairs (bigrams) and
    three-word phrases (trigrams) in saved verses.
    """

    def __init__(self, pattern=r"[a-zA-Z']+"):
        """
        Initialize the analyzer with a regex pattern for tokenization.

        Args:
            pattern: Regular expression pattern for matching words.
                    Default matches English words and contractions.

        Raises:
            FileNotFoundError: If the stop words file is not found.
            ValueError: If the stop words path exists but is not a file.
            re.error: If the provided pattern is not a valid regex.
        """
        self.word_analyzer = WordFrequencyAnalyzer(pattern)

    def _get_tokens(self, verses: list[dict]) -> list[str]:
        """
        Get tokenized words from verses.

        Args:
            verses: List of verse dictionaries, each containing a 'text' field.

        Returns:
            List of tokenized words (lowercased) with stop words removed.
        """
        text = WordFrequencyAnalyzer.get_verses_text(verses)
        if text is None:
            return []
        return self.word_analyzer.tokenize(text)

    def _generate_ngrams(self, tokens: list[str], n: int) -> list[tuple[str, ...]]:
        """
        Generate n-grams from a list of tokens.

        Args:
            tokens: List of tokenized words.
            n: Size of n-grams (2 for bigrams, 3 for trigrams, etc.).

        Returns:
            List of n-gram tuples.
        """
        if len(tokens) < n:
            return []
        return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

    def analyze_bigrams(self, verses: list[dict], top_n: int = 10) -> list[tuple[str, int]]:
        """
        Analyze and return the top N most frequent word pairs (bigrams).

        Args:
            verses: List of verse dictionaries, each containing a 'text' field.
            top_n: Number of top bigrams to return. Defaults to 10.

        Returns:
            A list of tuples (bigram_phrase, count) sorted by frequency (descending).
            Bigram phrases are formatted as "word1 word2".
            Returns an empty list if verses are empty or contain no text.
        """
        tokens = self._get_tokens(verses)
        if not tokens:
            return []

        bigrams = self._generate_ngrams(tokens, 2)
        bigram_counts = Counter(bigrams)

        formatted_bigrams = [
            (" ".join(bigram), count)
            for bigram, count in bigram_counts.most_common(top_n)
        ]

        return formatted_bigrams

    def analyze_trigrams(self, verses: list[dict], top_n: int = 10) -> list[tuple[str, int]]:
        """
        Analyze and return the top N most frequent three-word phrases (trigrams).

        Args:
            verses: List of verse dictionaries, each containing a 'text' field.
            top_n: Number of top trigrams to return. Defaults to 10.

        Returns:
            A list of tuples (trigram_phrase, count) sorted by frequency (descending).
            Trigram phrases are formatted as "word1 word2 word3".
            Returns an empty list if verses are empty or contain no text.
        """
        tokens = self._get_tokens(verses)
        if not tokens:
            return []

        trigrams = self._generate_ngrams(tokens, 3)
        trigram_counts = Counter(trigrams)

        formatted_trigrams = [
            (" ".join(trigram), count)
            for trigram, count in trigram_counts.most_common(top_n)
        ]

        return formatted_trigrams

    def show_phrase_analysis(
        self,
        verses: list[dict],
        visualize: bool = False,
        viz_display: str = "terminal"
    ) -> None:
        """
        Display formatted phrase analysis results including bigrams and trigrams.

        Args:
            verses: List of verse dictionaries, each containing a 'text' field.
            visualize: Whether to show visualizations
            viz_display: Display mode ("terminal", "export", or "both")
        """
        bigrams = self.analyze_bigrams(verses, top_n=20)
        trigrams = self.analyze_trigrams(verses, top_n=20)

        format_bigrams(bigrams)
        input("Press any key to continue...")
        format_trigrams(trigrams)
        spacing_after_output()

        if visualize:
            from app.analytics.visualizations import AnalyticsVisualizer
            viz = AnalyticsVisualizer()
            viz.plot_phrase_frequency(bigrams, title="Top Bigrams", display=viz_display)
            viz.plot_phrase_frequency(trigrams, title="Top Trigrams", display=viz_display)
