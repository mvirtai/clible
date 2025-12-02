from loguru import logger
from rich.console import Console, Group
from rich.text import Text
from rich.panel import Panel
from rich.padding import Padding

console = Console()

MAIN_MENU = {
    "title": "=== clible menu ===",
    "options": [
        "Fetch verse by reference",
        "Show all saved verses",
        "Analytic tools",
    ],
    "footer": "Exit",
}

ANALYTICS_MENU = {
    "title": "=== Analytic tools ===",
    "options": [
        "Search word",
        "Some-other-tool",
    ],
    "footer": "Back to main menu",
}


def prompt_menu_choice(menu: dict) -> int:
    render_menu(menu)
    while True:
        choice = input("Select option: ").strip()
        if choice.isdigit():
            return int(choice)
        console.print("[red]Please enter a number.[/red]")


def render_menu(menu: dict) -> None:
    title = Text(menu["title"], style="bold magenta")

    lines = []

    for i, option in enumerate(menu["options"], start=1):
        line = Text(f"[{i}] ", style="bold cyan")
        line.append(option)
        lines.append(line)
    
    footer_line = Text(f"[0] {menu['footer']}", style="bold red")

    body = Padding(
        Text("\n").join(lines + [Text("\n"), footer_line]),
        (1, 2)
    )

    panel = Panel(
        body,
        title=title,
        border_style="cyan",
        expand=False
    )

    console.print(panel)


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


def format_ref(book: str, chapter: str, verses: str) -> str:
    return f"{book.capitalize()} {chapter}:{verses}"