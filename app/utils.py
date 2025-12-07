from loguru import logger
from rich.console import Console, Group
from rich.text import Text
from rich.panel import Panel
from rich.padding import Padding
from app.db.queries import QueryDB
from collections import Counter
from typing import TypedDict

class VerseMatch(TypedDict):
    book: str
    chapter: int
    verse: int
    text: str

console = Console()


def render_search_results_info(data: list[VerseMatch], search_word: str) -> None:
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



def handle_search_word() -> list[VerseMatch]:
    word_input = input("Search word: ").strip()
    if not word_input:
        logger.info("Empty search, try again.")
        return []
    logger.info(f'Searching for "{word_input}"...')

    with QueryDB() as db:
        results = db.search_word(word_input)

    if not results:
        logger.info(f'No matches found for "{word_input}"')
        return results
    
    render_search_results_info(results, word_input)

    spacing_between_sections()
    for i, row in enumerate(results):
        ref = f'{row["book"]} {row["chapter"]}:{row["verse"]}'
        highlighted = highlight_word_in_text(row["text"], word_input)
        console.print(f'- [bold]{ref}[/bold]: {highlighted}')

    spacing_after_output()
    return results


def format_queries(queries: list[dict]) -> list:
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


def render_text_output(data: dict) -> Panel:
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


def format_ref(book: str, chapter: str, verses: str) -> str:
    return f"{book.capitalize()} {chapter}:{verses}"


def highlight_word_in_text(text: str, search_word: str) -> str:
    words = text.split(" ")
    highlighted_words = []

    for word in words:
        if word.lower() == search_word.lower():
        #    print(f"Match found: {word}") 
            highlighted_words.append(f"[bold magenta]{word}[/bold magenta]")
        else:
            highlighted_words.append(word)

    return " ".join(highlighted_words)
    

def add_vertical_spacing(lines: int = 1) -> None:
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