from rich.padding import Padding
from rich.text import Text
from rich.panel import Panel
from app.ui import console


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


def select_from_list(items: list[dict], prompt_text: str = "Select item") -> dict | None:
    """
    Display numbered list and let user select by number or ID.
    
    Args:
        items: List of dictionaries with 'id' key
        prompt_text: Text to show in prompt
        
    Returns:
        Selected item dict or None if cancelled/invalid
    """
    if not items:
        return None
    
    # Display numbered list
    for idx, item in enumerate(items, start=1):
        console.print(f"[bold cyan][{idx}][/bold cyan] ", end="")
        
        # Display item info based on type
        if 'name' in item:  # Session item
            status = "💾 Saved" if item.get('is_saved') else "⏱️  Temporary"
            console.print(f"{status} | ID: {item['id']} | Name: {item['name']}", end="")
            if 'scope' in item:
                console.print(f" | Scope: {item['scope']}")
            else:
                console.print()
        elif 'reference' in item:  # Query item
            verse_count = item.get('verse_count', 0)
            console.print(f"ID: {item['id']} | Reference: {item['reference']} | Verses: {verse_count}")
        else:  # Generic item
            console.print(f"ID: {item['id']}")
    
    # Get user input
    user_input = input(f"\n{prompt_text} (number or ID): ").strip()
    
    if not user_input:
        return None
    
    # Try to parse as number first
    try:
        idx = int(user_input)
        if 1 <= idx <= len(items):
            return items[idx - 1]
        else:
            console.print(f"[red]Invalid number. Please select 1-{len(items)}[/red]")
            return None
    except ValueError:
        # Not a number, try to match by ID
        for item in items:
            if item['id'] == user_input:
                return item
        
        console.print("[red]Invalid ID[/red]")
        return None


def parse_selection_range(input_string: str, max_value: int) -> list[int] | None:
    """Parse a comma-separated string of numbers or ranges into a list of integers."""
    result = []
    for part in input_string.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            start, end = map(int, part.split('-'))
            if start < 1 or end > max_value:
                console.print(f"[red]Invalid range {part}. Must be between 1 and {max_value}[/red]")
                return None
            result.extend(range(start, end + 1))
        else:
            try:
                value = int(part)
                if value < 1 or value > max_value:
                    console.print(f"[red]Invalid value {value}. Must be between 1 and {max_value}[/red]")
                    return None
                result.append(value)
            except ValueError:
                console.print(f"[red]Invalid value {part}. Must be a number[/red]")
                return None
    return result