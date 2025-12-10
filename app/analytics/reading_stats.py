from collections import Counter
from loguru import logger

from app.db.queries import QueryDB
from app.ui import console, format_reading_stats, format_top_books, format_top_chapters, spacing_after_output


class ReadingStatsAnalyzer:
    """
    Analyzes reading statistics from saved queries.
    
    Provides methods to calculate overall statistics, identify most
    frequently queried books and chapters, and display formatted results.
    """
    
    def __init__(self, db: QueryDB):
        """
        Initialize the analyzer with a database connection.
        
        Args:
            db: QueryDB instance for database queries.
        """
        self.db = db
    
    def get_overall_stats(self) -> dict[str, int]:
        """
        Calculate overall reading statistics.
        
        Returns:
            Dictionary containing:
            - total_verses: Total number of saved verses
            - unique_books: Number of unique books
            - unique_chapters: Number of unique (book, chapter) pairs
            - total_queries: Number of saved queries
        """
        total_verses = self.db.get_total_verse_count()
        unique_books = len(self.db.get_unique_books())
        unique_chapters = len(self.db.get_unique_chapters())
        
        # Get total queries count
        queries = self.db.show_all_saved_queries()
        total_queries = len(queries)
        
        return {
            "total_verses": total_verses,
            "unique_books": unique_books,
            "unique_chapters": unique_chapters,
            "total_queries": total_queries,
        }
    
    def get_top_books(self, n: int = 10) -> list[tuple[str, int]]:
        """
        Get the top N most frequently queried books.
        
        Args:
            n: Number of top books to return. Defaults to 10.
            
        Returns:
            List of tuples (book_name, count) sorted by count descending.
        """
        distribution = self.db.get_book_distribution()
        return distribution[:n]
    
    def get_top_chapters(self, n: int = 10) -> list[tuple[str, int, int]]:
        """
        Get the top N most frequently queried chapters.
        
        Args:
            n: Number of top chapters to return. Defaults to 10.
            
        Returns:
            List of tuples (book_name, chapter, count) sorted by count descending.
        """
        distribution = self.db.get_chapter_distribution()
        return distribution[:n]
    
    def show_reading_statistics(self) -> None:
        """
        Display formatted reading statistics including overall stats,
        top books, and top chapters.
        """
        overall_stats = self.get_overall_stats()
        top_books = self.get_top_books(10)
        top_chapters = self.get_top_chapters(10)
        
        format_reading_stats(overall_stats)
        input("Press any key to continue...")
        format_top_books(top_books)
        input("Press any key to continue...")
        format_top_chapters(top_chapters)
        spacing_after_output()

