import enum
from rich.console import Console, Group
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.padding import Padding
from rich import box


console = Console()

def render_text_output(data: dict) -> Panel:
    reference = data.get('reference', 'Unknown reference').lower().strip()
    translation = data.get('translation_name', '').strip()

    title = Text(reference.upper(), style="bold magenta")
    subtitle = Text(translation, style="italic cyan")

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
    return Panel(Padding(
        body, (2, 2)), 
        title=f"[bold magenta]{data.get('reference')}[/bold magenta]", 
        subtitle=f"[italic cyan]{data.get('translation_name')}[italic cyan]", 
        expand=False)


def format_url(book: str, chapter: str, verses: str) -> str:
    return f"https://bible-api.com/{book}+{chapter}:{verses}"


def format_ref(book: str, chapter: str, verses: str) -> str:
    return f"{book.capitalize()} {chapter}:{verses}"

