"""
UI rendering utilities for the clible application.

This module contains functions for rendering output to the terminal using Rich,
including formatting verses, queries, search results, and spacing utilities.
"""

from rich.console import Console, Group
from rich.text import Text
from rich.panel import Panel
from rich.padding import Padding
from collections import Counter
from typing import TypedDict

class VerseMatch(TypedDict):
    book: str
    chapter: int
    verse: int
    text: str

# Global console instance for terminal output
console = Console()


def render_text_output(data: dict) -> Panel:
    """
    Render verse data as a Rich Panel with formatted verses.
    
    Args:
        data: Dictionary containing 'verses', 'reference', and 'translation_name'
        
    Returns:
        A Rich Panel object ready to be printed
    """
    body_lines = []
    for verse in data.get("verses", []):
        num = f"{verse['verse']:>3}"
        raw = verse.get("text", "")
        text = " ".join(raw.split())
        line = Text()
        line.append(num, style="bold green")
        line.append("   ")
        line.append(text)
        body_lines.append(line)
    
    body = Group(*body_lines)
    
    reference = data.get('reference', 'Unknown reference')
    translation_name = data.get('translation_name', '')
    
    return Panel(Padding(
        body, (2, 2)), 
        title=f"[bold magenta]{reference}[/bold magenta]", 
        subtitle=f"[italic cyan]{translation_name}[/italic cyan]", 
        expand=False)


def format_queries(queries: list[dict]) -> list[str]:
    """
    Format a list of query dictionaries into displayable strings.
    
    Args:
        queries: List of query dictionaries with 'id', 'reference', 'verse_count', 'created_at'
        
    Returns:
        List of formatted query strings ready for display
    """
    spacing_between_sections()
    query_list = []
    if queries:
        console.print("[bold]Saved Queries[/bold]")
        spacing_after_output()
        
        for q in queries:
            query_id = q["id"]
            created_at = q["created_at"]
            ref = q["reference"]
            verse_count = q.get("verse_count", 0)
            query_str = f"[bold green]ID: {query_id}[/bold green] | [bold blue]Reference: {ref}[/bold blue] | [bold yellow]Verses: {verse_count}[/bold yellow] | [bold magenta]Saved at: {created_at}[/bold magenta]"
            query_list.append(query_str)
    else:
        console.print("[dim]No saved queries found.[/dim]")
        spacing_after_output()
    
    return query_list


def render_search_results_info(data: list[VerseMatch], search_word: str) -> None:
    """
    Render summary information about search results.
    
    Args:
        data: List of verse match dictionaries
        search_word: The word that was searched for
    """
    spacing_between_sections()
    total_count = len(data)
    book_counts = Counter(row['book'] for row in data)

    if total_count == 1:
        book_name = next(iter(book_counts))
        info_str = f"Found a match for the word '{search_word}' in the book of {book_name}"
    elif total_count >= 2:
        info_str = f'Found {total_count} matches for the word "{search_word}":'
    else:
        info_str = f'No matches found for the word "{search_word}"'
    
    console.print(info_str)
    spacing_after_output() 
    
    for book, count in book_counts.most_common():
        console.print(f"  • {book}: {count}", markup=False)


def highlight_word_in_text(text: str, search_word: str) -> str:
    """
    Highlight occurrences of a search word in text using Rich markup.
    
    Args:
        text: The text to search in
        search_word: The word to highlight
        
    Returns:
        Text string with Rich markup highlighting the search word
    """
    words = text.split(" ")
    highlighted_words = []

    for word in words:
        if word.lower() == search_word.lower():
            highlighted_words.append(f"[bold magenta]{word}[/bold magenta]")
        else:
            highlighted_words.append(word)

    return " ".join(highlighted_words)


def format_ref(book: str, chapter: str, verses: str) -> str:
    """
    Format a Bible reference string.
    
    Args:
        book: Book name
        chapter: Chapter number
        verses: Verse number(s)
        
    Returns:
        Formatted reference string (e.g., "John 3:16")
    """
    return f"{book.capitalize()} {chapter}:{verses}"



def format_word_frequency_analysis(results: list[tuple[str, int]]) -> None:
    """
    Format a list of word frequency analysis results into displayable strings.
    
    Args:
        results: List of tuples containing word and frequency
        
    Returns:
        List of formatted word frequency analysis strings ready for display
    """
    spacing_between_sections()
    if results:
        console.print("[bold]Word Frequency Analysis[/bold]")
        spacing_after_output()

        for word, frequency in results:
            console.print(f"[bold green]Word: {word}[/bold green] | [bold yellow]Frequency: {frequency}[/bold yellow]")
    else:
        console.print("[dim]No word frequency analysis results found.[/dim]")
        spacing_after_output()
    spacing_after_output()




def format_vocabulary_info(info: dict) -> None:
    """
    Format a dictionary of vocabulary information into displayable strings.
    
    Args:
        info: Dictionary containing vocabulary information
        
    Returns:
        List of formatted vocabulary information strings ready for display
    """
    spacing_between_sections()
    if info:
        console.print("[bold]Vocabulary Info[/bold]")
        spacing_after_output()
        
        for key, value in info.items():
            console.print(f"[bold green]Key: {key}[/bold green] | [bold yellow]Value: {value}[/bold yellow]")
    else:
        console.print("[dim]No vocabulary information found.[/dim]")
        spacing_after_output()
    spacing_after_output()  

def format_results(results: list[tuple[str, int]], info: dict) -> None:
    """
    Format a list of word frequency analysis results and vocabulary information into displayable strings.
    
    Args:
        results: List of tuples containing word and frequency
        info: Dictionary containing vocabulary information
    """
    spacing_between_sections()
    console.print("\n" + "Word Frequency Analysis:")
    format_word_frequency_analysis(results)
    console.print("\n" + "Vocabulary Info:")
    format_vocabulary_info(info)
    spacing_after_output()



# Spacing utilities

def add_vertical_spacing(lines: int = 1) -> None:
    """
    Add vertical spacing to the console output.
    
    Args:
        lines: Number of blank lines to add (max 2)
    """
    console.print("\n" * min(lines, 2))


def spacing_before_menu() -> None:
    """Add spacing before showing a menu."""
    add_vertical_spacing(1)


def spacing_after_output() -> None:
    """Add spacing after displaying output."""
    add_vertical_spacing(1)


def spacing_between_sections() -> None:
    """Add spacing between major sections."""
    add_vertical_spacing(2)
