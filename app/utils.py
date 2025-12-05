from loguru import logger
from rich.console import Console, Group
from rich.text import Text
from rich.panel import Panel
from rich.padding import Padding

console = Console()


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