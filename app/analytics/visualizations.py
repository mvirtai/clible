"""
Visualization module for analytics results.

Provides both terminal-based (plotext) and file export (matplotlib) options
for displaying word frequency, phrase analysis, and vocabulary statistics.
"""

import plotext as plt
from pathlib import Path
from typing import Literal
from datetime import datetime
from loguru import logger
import subprocess
import platform


class AnalyticsVisualizer:
    """
    Visualizer for analytics results.
    
    Supports both terminal display (plotext) and file export (matplotlib).
    """
    
    def __init__(self, export_dir: Path = None):
        """
        Initialize visualizer with export directory.
        
        Args:
            export_dir: Directory for exported charts. Defaults to data/charts/
        """
        self.export_dir = export_dir or Path("data/charts")
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_word_frequency(
        self, 
        word_freq: list[tuple[str, int]], 
        display: Literal["terminal", "export", "both"] = "terminal",
        export_format: Literal["png", "html"] = "png",
        top_n: int = 15
    ) -> Path | None:
        """
        Plot word frequency as horizontal bar chart.
        
        Args:
            word_freq: List of (word, count) tuples
            display: Where to display ("terminal", "export", or "both")
            export_format: Export format ("png" or "html")
            top_n: Number of top words to display
            
        Returns:
            Path to exported file if export was requested, None otherwise
        """
        if not word_freq:
            logger.warning("No word frequency data to visualize")
            return None
        
        # Limit to top N words
        top_words = word_freq[:top_n]
        words = [w[0] for w in top_words]
        counts = [w[1] for w in top_words]
        
        # Terminal display
        if display in ["terminal", "both"]:
            plt.clear_figure()
            plt.bar(words, counts, orientation='h', width=0.3)
            plt.title("Word Frequency Analysis")
            plt.xlabel("Frequency")
            plt.ylabel("Words")
            plt.theme("pro")
            plt.show()
        
        # File export
        exported_file = None
        if display in ["export", "both"]:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            export_path = self.export_dir / "word_frequency"
            export_path.mkdir(parents=True, exist_ok=True)
            
            if export_format == "html":
                filename = export_path / f"{timestamp}_word_freq.html"
                plt.clear_figure()
                plt.bar(words, counts, orientation='h', width=0.3)
                plt.title("Word Frequency Analysis")
                plt.xlabel("Frequency")
                plt.ylabel("Words")
                plt.theme("pro")
                plt.save_fig(str(filename))
                exported_file = filename
                logger.info(f"Saved HTML chart: {filename}")
            else:  # PNG
                filename = export_path / f"{timestamp}_word_freq.png"
                self._export_matplotlib_bar(
                    words, counts, 
                    "Word Frequency Analysis",
                    "Frequency",
                    "Words",
                    filename
                )
                exported_file = filename
                logger.info(f"Saved PNG chart: {filename}")
        
        return exported_file
    
    def plot_phrase_frequency(
        self,
        phrases: list[tuple[str, int]],
        title: str = "Phrase Frequency",
        display: Literal["terminal", "export", "both"] = "terminal",
        export_format: Literal["png", "html"] = "png",
        top_n: int = 15
    ) -> Path | None:
        """
        Plot phrase frequency (bigrams/trigrams) as horizontal bar chart.
        
        Args:
            phrases: List of (phrase, count) tuples
            title: Chart title
            display: Where to display
            export_format: Export format
            top_n: Number of top phrases to display
            
        Returns:
            Path to exported file if export was requested, None otherwise
        """
        if not phrases:
            logger.warning("No phrase data to visualize")
            return None
        
        # Limit to top N phrases
        top_phrases = phrases[:top_n]
        phrase_texts = [p[0] for p in top_phrases]
        counts = [p[1] for p in top_phrases]
        
        # Terminal display
        if display in ["terminal", "both"]:
            plt.clear_figure()
            plt.bar(phrase_texts, counts, orientation='h', width=0.3)
            plt.title(title)
            plt.xlabel("Frequency")
            plt.ylabel("Phrases")
            plt.theme("pro")
            plt.show()
        
        # File export
        exported_file = None
        if display in ["export", "both"]:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            export_path = self.export_dir / "phrases"
            export_path.mkdir(parents=True, exist_ok=True)
            
            # Sanitize title for filename
            safe_title = title.lower().replace(" ", "_")
            
            if export_format == "html":
                filename = export_path / f"{timestamp}_{safe_title}.html"
                plt.clear_figure()
                plt.bar(phrase_texts, counts, orientation='h', width=0.3)
                plt.title(title)
                plt.xlabel("Frequency")
                plt.ylabel("Phrases")
                plt.theme("pro")
                plt.save_fig(str(filename))
                exported_file = filename
                logger.info(f"Saved HTML chart: {filename}")
            else:  # PNG
                filename = export_path / f"{timestamp}_{safe_title}.png"
                self._export_matplotlib_bar(
                    phrase_texts, counts,
                    title,
                    "Frequency",
                    "Phrases",
                    filename
                )
                exported_file = filename
                logger.info(f"Saved PNG chart: {filename}")
        
        return exported_file
    
    def plot_vocabulary_stats(
        self,
        vocab_info: dict,
        display: Literal["terminal", "export", "both"] = "terminal",
        export_format: Literal["png", "html"] = "png"
    ) -> Path | None:
        """
        Display vocabulary statistics as bar chart.
        
        Args:
            vocab_info: Dictionary with total_tokens, vocabulary_size, type_token_ratio
            display: Where to display
            export_format: Export format
            
        Returns:
            Path to exported file if export was requested, None otherwise
        """
        if not vocab_info:
            logger.warning("No vocabulary data to visualize")
            return None
        
        labels = [
            "Total Tokens",
            "Unique Words",
            f"TTR ({vocab_info.get('type_token_ratio', 0):.3f})"
        ]
        values = [
            vocab_info.get('total_tokens', 0),
            vocab_info.get('vocabulary_size', 0),
            int(vocab_info.get('type_token_ratio', 0) * 100)  # Scale for visibility
        ]
        
        # Terminal display
        if display in ["terminal", "both"]:
            plt.clear_figure()
            plt.bar(labels, values)
            plt.title("Vocabulary Statistics")
            plt.ylabel("Count / Percentage")
            plt.theme("pro")
            plt.show()
        
        # File export
        exported_file = None
        if display in ["export", "both"]:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            export_path = self.export_dir / "word_frequency"
            export_path.mkdir(parents=True, exist_ok=True)
            
            if export_format == "html":
                filename = export_path / f"{timestamp}_vocab_stats.html"
                plt.clear_figure()
                plt.bar(labels, values)
                plt.title("Vocabulary Statistics")
                plt.ylabel("Count / Percentage")
                plt.theme("pro")
                plt.save_fig(str(filename))
                exported_file = filename
                logger.info(f"Saved HTML chart: {filename}")
            else:  # PNG
                filename = export_path / f"{timestamp}_vocab_stats.png"
                self._export_matplotlib_bar_vertical(
                    labels, values,
                    "Vocabulary Statistics",
                    "Metrics",
                    "Count / Percentage",
                    filename
                )
                exported_file = filename
                logger.info(f"Saved PNG chart: {filename}")
        
        return exported_file
    
    def _export_matplotlib_bar(
        self, 
        labels: list[str], 
        values: list[int],
        title: str,
        xlabel: str,
        ylabel: str,
        filename: Path
    ):
        """Export horizontal bar chart using matplotlib."""
        try:
            import matplotlib.pyplot as mpl_plt
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            
            fig, ax = mpl_plt.subplots(figsize=(10, 6))
            ax.barh(labels, values, color='steelblue')
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.grid(axis='x', alpha=0.3)
            
            mpl_plt.tight_layout()
            mpl_plt.savefig(filename, dpi=300, bbox_inches='tight')
            mpl_plt.close(fig)
            
        except Exception as e:
            logger.error(f"Failed to export matplotlib chart: {e}")
    
    def _export_matplotlib_bar_vertical(
        self,
        labels: list[str],
        values: list[int],
        title: str,
        xlabel: str,
        ylabel: str,
        filename: Path
    ):
        """Export vertical bar chart using matplotlib."""
        try:
            import matplotlib.pyplot as mpl_plt
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            
            fig, ax = mpl_plt.subplots(figsize=(8, 6))
            ax.bar(labels, values, color='steelblue')
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            
            mpl_plt.tight_layout()
            mpl_plt.savefig(filename, dpi=300, bbox_inches='tight')
            mpl_plt.close(fig)
            
        except Exception as e:
            logger.error(f"Failed to export matplotlib chart: {e}")
    
    @staticmethod
    def open_in_viewer(filepath: Path) -> bool:
        """
        Open file in default system viewer.
        
        Args:
            filepath: Path to file to open
            
        Returns:
            True if successful, False otherwise
        """
        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", str(filepath)], check=True)
            elif system == "Windows":
                subprocess.run(["start", str(filepath)], shell=True, check=True)
            else:  # Linux
                subprocess.run(["xdg-open", str(filepath)], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to open file in viewer: {e}")
            return False
