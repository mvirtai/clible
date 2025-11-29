from loguru import logger
from rich.console import Console, Group
from rich.text import Text
from rich.panel import Panel
from rich.padding import Padding

from app.validations.validations import validate_books



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
        subtitle=f"[italic cyan]{data.get('translation_name')}[/italic cyan]", 
        expand=False)


def format_url(base_url: str, url_params: list[str]) -> str:
    logger.debug(base_url)
    book, chapter = url_params[0].strip().lower(), url_params[1].strip().lower()
    logger.debug(f"book: {book}, chapter: {chapter}")
    
    if len[0] != "data":
        if len(url_params == 3):
            verses = url_params[2].strip.lower()
    
    

def format_ref(book: str, chapter: str, verses: str) -> str:
    return f"{book.capitalize()} {chapter}:{verses}"


if __name__ == "__main__":
    url = format_url(base_url="https://test.com", url_params=["john", "3", "16"])
    logger.debug("url:", url)