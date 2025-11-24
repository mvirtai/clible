from rich.console import Console, Group
from rich.text import Text
from rich.panel import Panel
from rich.align import Align


console = Console()

def render_text_output(data: dict) -> Panel:
    reference = data.get('reference', 'Unknown reference').lower().strip()
    translation = data.get('translation_name', '').strip()
    header = Text(reference, style='bold cyan')

    if translation:
        header.append(f" • {translation}", style="italic green")
    
    body_lines = []

    for verse in data.get('verses', []):
        num = f"{verse['verse']:>3}"
        text = verse.get('text', '').strip()
        body_lines.append(Text(f"{num}  {text}"))
    
    body = Group(*body_lines)
    return Panel(body, title=reference, subtitle=translation, expand=False)


def format_url(book: str, chapter: str, verses: str) -> str:
    return f"https://bible-api.com/{book}+{chapter}:{verses}"


def format_ref(book: str, chapter: str, verses: str) -> str:
    return f"{book.capitalize()} {chapter}:{verses}"

