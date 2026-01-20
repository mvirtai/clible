from rich.padding import Padding
from rich.text import Text
from rich.panel import Panel
from simple_term_menu import TerminalMenu
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


def select_from_list(items: list[dict] | list[str], prompt_text: str = "Select item") -> dict | str | None:
    """
    Display numbered list and let user select by number or ID/name.
    
    Args:
        items: List of dictionaries with 'id' key OR list of strings
        prompt_text: Text to show in prompt
        
    Returns:
        Selected item dict/str or None if cancelled/invalid
    """
    if not items:
        return None
    
    # Handle string lists (like books)
    is_string_list = isinstance(items[0], str) if items else False
    original_items = items  # Keep reference to original for return value
    
    if is_string_list:
        # Convert strings to dicts for uniform handling
        # Use book name as both id and name
        items = [{'id': item, 'name': item, '_is_string': True} for item in items]
    
    # Display numbered list
    for idx, item in enumerate(items, start=1):
        console.print(f"[bold cyan][{idx}][/bold cyan] ", end="")
        
        # Display item info based on type
        if item.get('_is_string'):  # String item (book)
            console.print(item['name'])
        elif 'name' in item and 'is_saved' in item:  # Session item
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
            selected = items[idx - 1]
            # Return original format
            if is_string_list:
                return selected['name']  # Return string
            return selected  # Return dict
        else:
            console.print(f"[red]Invalid number. Please select 1-{len(items)}[/red]")
            return None
    except ValueError:
        # Not a number, try to match by ID or name
        for item in items:
            if item['id'] == user_input or (is_string_list and item['name'].lower() == user_input.lower()):
                if is_string_list:
                    return item['name']  # Return string
                return item  # Return dict
        
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


def select_interactive(
    items: list[str],
    title: str = "Select an option",
    multi_select: bool = False,
    show_search_hint: bool = True,
) -> str | list[str] | None:
    """
    Interactive selection menu with arrow key navigation.
    
    Args:
        items: List of string options to display
        title: Title shown above the menu
        multi_select: If True, allows selecting multiple items with SPACE
        show_search_hint: If True, shows search hint in title
        
    Returns:
        Selected item(s) or None if cancelled (ESC/q)
        - Single select: returns str or None
        - Multi select: returns list[str] or None
    """
    if not items:
        console.print("[yellow]No items to select from.[/yellow]")
        return None
    
    # Filter out empty strings
    filtered_items = [item for item in items if item]
    if not filtered_items:
        console.print("[yellow]No valid items to select from.[/yellow]")
        return None
    
    # Build title with hints
    if multi_select:
        hint = "↑↓ navigate | SPACE select | ENTER confirm | ESC cancel"
    else:
        hint = "↑↓ navigate | ENTER select | ESC cancel"
    
    if show_search_hint:
        hint += " | / search"
    
    full_title = f"{title}\n{hint}"
    
    menu = TerminalMenu(
        filtered_items,
        title=full_title,
        multi_select=multi_select,
        show_multi_select_hint=multi_select,
        multi_select_select_on_accept=False,
        multi_select_empty_ok=False,
        search_key="/",
        show_search_hint=show_search_hint,
    )
    
    result = menu.show()
    
    if result is None:
        return None
    
    if multi_select:
        if isinstance(result, tuple):
            return [filtered_items[i] for i in result]
        return None
    else:
        return filtered_items[result]