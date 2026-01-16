from collections import Counter
from loguru import logger
import re
import json
from pathlib import Path

from app.db.queries import QueryDB
from app.ui import console, format_results

class WordFrequencyAnalyzer:
    """
    Analyzes word frequency in biblical verses.
    
    Provides methods to tokenize text, filter stop words, and compute
    word frequency statistics including vocabulary size and type-token ratios.
    """
    
    @staticmethod
    def load_stop_words(path: str | Path) -> set[str]:
        """
        Load stop words from a JSON file.
        
        Args:
            path: Path to the JSON file containing stop words as a list.
            
        Returns:
            A set of normalized (lowercased, stripped) stop words.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        with open(path, "r", encoding="utf-8") as f:
            words = json.load(f)
        return {w.strip().lower() for w in words if w and isinstance(w, str)}


    @staticmethod
    def get_verses_text(verses: list[dict]) -> str | None:
        """
        Concatenate the 'text' field from each verse dictionary into a single string.
        Returns None if the input list is empty or all items are None.
        """
        if not verses or all(v is None for v in verses):
            return None
        return " ".join(
            v.get("text", "") for v in verses if v is not None
        )


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
        root = Path(__file__).resolve().parents[2]
        path = Path("data/stop_words.json")
        if not path.is_absolute():
            path = root / path
        
        if not path.exists():
            raise FileNotFoundError(f"Stop words file not found: {path}")
        
        if not path.is_file():
            raise ValueError(f"Path exists but is not a file: {path}")
        
        self.stop_words = self.load_stop_words(path)
        self.pattern = re.compile(pattern)
        

    def tokenize(self, text: str) -> list[str]:
        """
        Tokenize the input text into words, filtering out stop words.
        
        Text is converted to lowercase and matched against the configured
        regex pattern. Stop words are removed from the results.
        
        Args:
            text: The input text to tokenize.
            
        Returns:
            A list of tokenized words (lowercased) with stop words removed.
        """
        tokens = self.pattern.findall(text.lower())
        return [t for t in tokens if t not in self.stop_words]
    

    def analyze_top(self, verses: list[dict], top_n: int = 10) -> list[tuple[str, int]]:
        """
        Analyze and return the top N most frequent words in the verses.
        
        Args:
            verses: List of verse dictionaries, each containing a 'text' field.
            top_n: Number of top words to return. Defaults to 10.
            
        Returns:
            A list of tuples (word, count) sorted by frequency (descending).
            Returns an empty list if verses are empty or contain no text.
        """
        text = self.get_verses_text(verses)
        if text is None:
            return []
        tokens = self.tokenize(text)

        return Counter(tokens).most_common(top_n)
    

    def count_vocabulary_size(self, verses: list[dict]) -> dict[str, float]:
        """
        Compute vocabulary statistics for the given verses.
        
        Calculates total token count, unique vocabulary size, and type-token
        ratio. The type-token ratio indicates vocabulary diversity (higher
        means more varied vocabulary, lower means more repetition).
        
        Args:
            verses: List of verse dictionaries, each containing a 'text' field.
            
        Returns:
            A dictionary containing:
            - total_tokens: Number of tokens after stop-word removal
            - vocabulary_size: Count of unique tokens
            - type_token_ratio: Ratio of unique tokens to total tokens (0-1)
            
            Returns an empty dict if verses are empty or contain no text.
        """
        text = self.get_verses_text(verses)
        if text is None:
            return {}
        tokens = self.tokenize(text)
        total_tokens = len(tokens)
        vocabulary_size = len(set(tokens))
        type_token_ratio = vocabulary_size / total_tokens if total_tokens else 0.0
        type_token_ratio = round(type_token_ratio, 3)

        return {
            "total_tokens": total_tokens,
            "vocabulary_size": vocabulary_size,
            "type_token_ratio": type_token_ratio,
        }

    
    def show_word_frequency_analysis(
        self, 
        verses: list[dict],
        visualize: bool = False,
        viz_display: str = "terminal"
    ) -> None:
        """Show word frequency analysis with optional visualization."""
        verses_text = self.get_verses_text(verses)
        if verses_text is None:
            return
        
        top_words = self.analyze_top(verses, top_n=20)
        vocab_info = self.count_vocabulary_size(verses)
        
        # Existing text output
        format_results(top_words, vocab_info)
        
        # NEW: Optional visualization
        if visualize:
            from app.analytics.visualizations import AnalyticsVisualizer
            viz = AnalyticsVisualizer()
            viz.plot_word_frequency(top_words, display=viz_display)
            viz.plot_vocabulary_stats(vocab_info, display=viz_display)


if __name__ == "__main__":
    with QueryDB() as db:
        all_saved_verses = db.show_all_saved_queries()
        for verse in all_saved_verses:
            console.print(f"  ID: {verse['id']} | Reference: {verse['reference']} | Verses: {verse['verse_count']}")
        # Prompt the user to input a query ID
        # query_id = input("Give ID: ").strip()
        # Retrieve verses matching the given query ID
        verse_data = db.get_verses_by_query_id('c1f6940d')
    analyzer = WordFrequencyAnalyzer()
    top_words = analyzer.analyze_top(verse_data, top_n=20)
    console.print("\n" + "    Top words:")
    console.print(top_words)
    console.print("\n" + "Vocabulary info:")
    vocab_info = analyzer.count_vocabulary_size(verse_data)
    console.print(vocab_info)
