"""
Translation comparison module for clible.

This module provides functionality to compare Bible verses across different translations,
displaying them side-by-side for easy comparison.

Currently supports comparison of two translations at a time.
"""

from rich.table import Table
from rich.panel import Panel
from loguru import logger
import re
from difflib import SequenceMatcher

from app.api import fetch_by_reference
from app.ui import console, spacing_between_sections


# Available Bible translations supported by bible-api.com
AVAILABLE_TRANSLATIONS = [
    "web",   # World English Bible (default)
    "kjv",   # King James Version
    "bbe",   # Bible in Basic English
    "asv",   # American Standard Version
    "ylt",   # Young's Literal Translation
    "niv",   # New International Version (if supported)
]


def fetch_verse_comparison(
    book: str,
    chapter: str,
    verses: str | None = None,
    translation1: str = "web",
    translation2: str = "kjv"
) -> dict | None:
    """
    Fetch a verse (or range of verses) from the API in two different translations.
    
    Fetches the same verse(s) from two different translations and returns them
    in a structured format for comparison. If the verse range spans multiple
    verses, all verses are included.
    
    Args:
        book: Book name (e.g., "John", "Genesis")
        chapter: Chapter number as string (e.g., "3")
        verses: Optional verse number(s) as string (e.g., "16" or "16-18").
                If None, fetches entire chapter.
        translation1: First translation identifier (default: "web")
        translation2: Second translation identifier (default: "kjv")
    
    Returns:
        Dictionary containing:
        - "reference": The verse reference string (e.g., "John 3:16")
        - "translation1": Dict with translation1 data (reference, verses list, translation_name, translation_id)
        - "translation2": Dict with translation2 data (same structure)
        None if either fetch fails
    
    Example:
        >>> result = fetch_verse_comparison("John", "3", "16", "web", "kjv")
        >>> result["translation1"]["verses"][0]["text"]
        'For God so loved the world...'
    """
    if not book or not chapter:
        logger.error("Book and chapter are required")
        return None
    
    # Fetch first translation
    verse_data_1 = fetch_by_reference(book, chapter, verses, translation=translation1)
    if not verse_data_1:
        logger.error(f"Failed to fetch verse in translation '{translation1}'")
        return None
    
    # Fetch second translation
    verse_data_2 = fetch_by_reference(book, chapter, verses, translation=translation2)
    if not verse_data_2:
        logger.error(f"Failed to fetch verse in translation '{translation2}'")
        return None
    
    # Extract reference from first translation
    reference = verse_data_1.get("reference", f"{book} {chapter}" + (f":{verses}" if verses else ""))
    
    return {
        "reference": reference,
        "translation1": {
            "reference": reference,
            "verses": verse_data_1.get("verses", []),
            "translation_name": verse_data_1.get("translation_name", translation1.upper()),
            "translation_id": verse_data_1.get("translation_id", translation1),
        },
        "translation2": {
            "reference": reference,
            "verses": verse_data_2.get("verses", []),
            "translation_name": verse_data_2.get("translation_name", translation2.upper()),
            "translation_id": verse_data_2.get("translation_id", translation2),
        },
    }


def render_side_by_side_comparison(comparison_data: dict) -> None:
    """
    Render a side-by-side comparison of verses from two translations.
    
    Displays verses in a table format with two columns, one for each translation.
    Each verse is shown on its own row with verse number and text. If there are
    multiple verses, they are displayed separately.
    
    Args:
        comparison_data: Dictionary returned by fetch_verse_comparison containing:
            - "reference": Verse reference string
            - "translation1": Dict with first translation data
            - "translation2": Dict with second translation data
    
    Example:
        >>> data = fetch_verse_comparison("John", "3", "16", "web", "kjv")
        >>> render_side_by_side_comparison(data)
        # Displays a table with WEB and KJV translations side-by-side
    """
    if not comparison_data:
        console.print("[red]No comparison data provided[/red]")
        return
    
    reference = comparison_data.get("reference", "Unknown reference")
    trans1_data = comparison_data.get("translation1", {})
    trans2_data = comparison_data.get("translation2", {})
    
    trans1_verses = trans1_data.get("verses", [])
    trans2_verses = trans2_data.get("verses", [])
    trans1_name = trans1_data.get("translation_name", "Translation 1")
    trans2_name = trans2_data.get("translation_name", "Translation 2")
    
    if not trans1_verses or not trans2_verses:
        console.print("[yellow]No verses found in one or both translations[/yellow]")
        return
    
    spacing_between_sections()
    
    # Create table for side-by-side display
    table = Table(
        title=f"[bold cyan]{reference}[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
        border_style="cyan",
        expand=True
    )
    
    # Add columns
    table.add_column(
        f"[bold green]{trans1_name}[/bold green]",
        style="green",
        no_wrap=False,
        width=50
    )
    table.add_column(
        f"[bold blue]{trans2_name}[/bold blue]",
        style="blue",
        no_wrap=False,
        width=50
    )
    
    # Determine max verses to display (handle cases where counts differ)
    max_verses = max(len(trans1_verses), len(trans2_verses))
    
    # Add each verse as a row
    for i in range(max_verses):
        verse1 = trans1_verses[i] if i < len(trans1_verses) else None
        verse2 = trans2_verses[i] if i < len(trans2_verses) else None
        
        # Format verse 1
        if verse1:
            verse_num1 = verse1.get("verse", "")
            text1 = verse1.get("text", "").strip()
            verse_text1 = f"[bold green][{verse_num1}][/bold green] {text1}"
        else:
            verse_text1 = "[dim]No verse[/dim]"
        
        # Format verse 2
        if verse2:
            verse_num2 = verse2.get("verse", "")
            text2 = verse2.get("text", "").strip()
            verse_text2 = f"[bold blue][{verse_num2}][/bold blue] {text2}"
        else:
            verse_text2 = "[dim]No verse[/dim]"
        
        table.add_row(verse_text1, verse_text2)
    
    console.print(table)
    spacing_between_sections()
    
    # Calculate and display statistics
    stats = calculate_translation_differences(comparison_data)
    if stats:
        # Display similarity statistics
        console.print("[bold cyan]Translation Statistics:[/bold cyan]")
        console.print(f"  Overall Similarity: [yellow]{stats['similarity_ratio']:.1%}[/yellow]")
        console.print(f"  Word Count ({trans1_name}): [green]{stats['word_count_1']}[/green]")
        console.print(f"  Word Count ({trans2_name}): [blue]{stats['word_count_2']}[/blue]")
        console.print(f"  Common Vocabulary: [magenta]{stats['common_words_count']}[/magenta] words")
        console.print(f"  Unique to {trans1_name}: [green]{stats['unique_count_1']}[/green] words")
        console.print(f"  Unique to {trans2_name}: [blue]{stats['unique_count_2']}[/blue] words")
        
        # Show some unique words if available
        if stats.get('unique_words_1'):
            unique_sample_1 = ', '.join(stats['unique_words_1'][:10])
            console.print(f"  Sample unique words ({trans1_name}): [dim]{unique_sample_1}[/dim]")
        if stats.get('unique_words_2'):
            unique_sample_2 = ', '.join(stats['unique_words_2'][:10])
            console.print(f"  Sample unique words ({trans2_name}): [dim]{unique_sample_2}[/dim]")
        
        spacing_between_sections()


def calculate_translation_differences(comparison_data: dict) -> dict:
    """
    Calculate statistical differences between two translations.
    
    Analyzes word-level differences, similarity ratios, and unique vocabulary
    between two translations of the same verses.
    
    Args:
        comparison_data: Dictionary returned by fetch_verse_comparison containing:
            - "reference": Verse reference string
            - "translation1": Dict with first translation data
            - "translation2": Dict with second translation data
            
    Returns:
        Dictionary containing:
            - "similarity_ratio": Overall text similarity (0.0 to 1.0)
            - "word_count_1": Total word count in translation 1
            - "word_count_2": Total word count in translation 2
            - "unique_words_1": Words only in translation 1
            - "unique_words_2": Words only in translation 2
            - "common_words": Words in both translations
            - "verse_similarities": List of similarity ratios per verse
    """
    if not comparison_data:
        return {}
    
    trans1_verses = comparison_data.get("translation1", {}).get("verses", [])
    trans2_verses = comparison_data.get("translation2", {}).get("verses", [])
    
    if not trans1_verses or not trans2_verses:
        return {}
    
    # Concatenate all verse texts
    text1 = " ".join(v.get("text", "").strip() for v in trans1_verses)
    text2 = " ".join(v.get("text", "").strip() for v in trans2_verses)
    
    # Calculate overall similarity
    similarity_ratio = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    # Tokenize into words (simple approach - includes alphanumeric)
    word_pattern = re.compile(r'\b[a-z0-9\']+\b', re.IGNORECASE)
    words1 = set(word.lower() for word in word_pattern.findall(text1))
    words2 = set(word.lower() for word in word_pattern.findall(text2))
    
    # Find unique and common words
    unique_words_1 = words1 - words2
    unique_words_2 = words2 - words1
    common_words = words1 & words2
    
    # Count total words (including duplicates)
    all_words1 = word_pattern.findall(text1)
    all_words2 = word_pattern.findall(text2)
    
    # Calculate per-verse similarities
    verse_similarities = []
    for i in range(min(len(trans1_verses), len(trans2_verses))):
        v1_text = trans1_verses[i].get("text", "").strip()
        v2_text = trans2_verses[i].get("text", "").strip()
        verse_sim = SequenceMatcher(None, v1_text.lower(), v2_text.lower()).ratio()
        verse_similarities.append({
            "verse": trans1_verses[i].get("verse"),
            "similarity": verse_sim
        })
    
    return {
        "similarity_ratio": similarity_ratio,
        "word_count_1": len(all_words1),
        "word_count_2": len(all_words2),
        "unique_words_1": sorted(list(unique_words_1))[:20],  # Top 20 for display
        "unique_words_2": sorted(list(unique_words_2))[:20],  # Top 20 for display
        "common_words_count": len(common_words),
        "unique_count_1": len(unique_words_1),
        "unique_count_2": len(unique_words_2),
        "verse_similarities": verse_similarities
    }