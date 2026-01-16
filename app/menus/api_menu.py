# app/menus/api_menu.py
import click
import time
from loguru import logger

from app.ui import (
    console, render_text_output, spacing_before_menu, spacing_after_output,
    spacing_between_sections, render_book_list,
)
from app.menus.menu_utils import prompt_menu_choice
from app.menus.menus import MAIN_MENU, API_MENU, ANALYTICS_MENU
from app.validations.click_params import BookParam, ChapterParam, VersesParam
from app.api import fetch_by_reference, fetch_book_list
from app.db.queries import QueryDB


def run_api_menu(output: str):
    """Handle the Fetch from API submenu."""
    while True:
        spacing_before_menu()
        choice = prompt_menu_choice(API_MENU)

        if choice == 1:
            verse_data = handle_fetch_by_ref('v')
            if verse_data:
                spacing_between_sections()
                console.print(render_text_output(verse_data))
                handle_save(verse_data)
            else:
                logger.error("Failed to fetch verse. Check logs for details.")
            spacing_after_output()
        elif choice == 2:
            chapter_data = handle_fetch_by_ref('c')
            if chapter_data:
                spacing_between_sections()
                console.print(render_text_output(chapter_data))
                handle_save(chapter_data)
            else:
                logger.error("Failed to fetch chapter. Check logs for details.")
            spacing_after_output()
        elif choice == 3:
            random_verse_data = handle_fetch_by_ref('r')
            if random_verse_data:
                spacing_between_sections()
                console.print(render_text_output(random_verse_data))
                handle_save(random_verse_data)
            else:
                logger.error("Failed to fetch random verse. Check logs for details.")
            spacing_after_output()
        elif choice == 4:
            handle_fetch_multiple_books()
            spacing_after_output()
        elif choice == 0:
            return



def handle_fetch_by_ref(mode: str) -> dict | None:
    if mode == 'v':
        # Fetch verse by reference
        console.print("\n[bold cyan]Available books:[/bold cyan]")
        render_book_list()
        console.print()
        
        book = click.prompt("Book", type=BookParam())
        chapter = click.prompt("Chapter", type=ChapterParam())
        verses = click.prompt("Verses", type=VersesParam())

        data = fetch_by_reference(book, chapter, verses)
        word = 'verse(s)'
    elif mode == 'c':
        # Fetch chapter by reference
        console.print("\n[bold cyan]Available books:[/bold cyan]")
        render_book_list()
        console.print()
        
        book = click.prompt("Book", type=BookParam())
        chapter = click.prompt("Chapter", type=ChapterParam())

        data = fetch_by_reference(book, chapter, None)
        word = 'chapter'
    elif mode == 'r':
        # Fetch random verse
        data = fetch_by_reference(None, None, None, True)
        word = 'random verse'
    else:
        logger.error(f"Invalid mode: {mode}. Must be 'v', 'c', or 'r'")
        return None

    if not data:
        logger.error("Failed to fetch verse. Check logs for details.")
        return None
    
    logger.info(f"Fetched {word} successfully")
    return data


def handle_save(data: dict):
    """
    Save fetched verse data to database and optionally link to active session.
    
    If user has an active session, the query will be linked to that session.
    Query is always saved permanently, even if no session is active.
    """
    choice = click.confirm("Do you want to save result the result? [y/N] ", default=True)

    if not choice:
        logger.info("Result not saved")
        return

    try:
        with QueryDB() as db:
            from app.state import AppState
            state = AppState()
            session_id = state.current_session_id

            # Save query permanently to queries table (returns query_id)
            query_id = db.save_query(data)
            
            # Link query to active session if one exists
            if session_id:
                db.add_query_to_session(session_id, query_id)
                logger.info(f"Result saved and linked to session (id={query_id})")
                console.print(f"[green]Result saved and linked to session (id={query_id})[/green]")
            else:
                logger.info(f"Result saved (id={query_id}) - no active session")
                console.print(f"[green]Result saved (id={query_id})[/green]")
                console.print("[dim]Note: No active session - query not linked to session[/dim]")
                    
    except Exception as e:
        logger.error(f"Failed to save result: {e}")
        console.print(f"[red]Failed to save result: {e}[/red]")


def handle_fetch_multiple_books():
    """
    Display books with IDs and names, allow user to select multiple by ID.
    Fetches all chapters for selected books.
    """
    console.print("\n[bold cyan]Available books:[/bold cyan]")
    
    # Fetch and display book list
    books = fetch_book_list()
    if not books:
        console.print("[red]Failed to fetch book list from API[/red]")
        return
    
    # Display books with IDs and names
    for book in books:
        book_id = book.get('id', 'N/A')
        book_name = book.get('name', 'Unknown')
        console.print(f"  [bold green][{book_id}][/bold green] [bold cyan]{book_name}[/bold cyan]")
    
    console.print()
    console.print("[dim]Enter book IDs separated by commas (e.g., gen,exod,matt)[/dim]")
    console.print("[dim]Or press Enter to cancel[/dim]")
    
    # Get user input
    user_input = input("\nBook IDs: ").strip()
    
    if not user_input:
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Parse selected IDs
    selected_ids = [id.strip().lower() for id in user_input.split(',')]
    
    # Validate and get selected books
    selected_books = []
    for book in books:
        if book.get('id', '').lower() in selected_ids:
            selected_books.append(book)
    
    if not selected_books:
        console.print("[red]No valid books selected[/red]")
        return
    
    console.print(f"\n[bold green]Selected {len(selected_books)} book(s):[/bold green]")
    for book in selected_books:
        console.print(f"  • {book['name']}")
    
    # Ask how many chapters to fetch per book
    console.print("\n[dim]Options:[/dim]")
    console.print("  [dim]• Enter a chapter range (e.g., 1-5 or 1)[/dim]")
    console.print("  [dim]• Enter 'all' to fetch all available chapters (tries up to 150)[/dim]")
    
    chapter_input = input("\nChapters to fetch: ").strip().lower()
    
    if not chapter_input:
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Parse chapter range
    chapters_to_fetch = []
    if chapter_input == 'all':
        # Try chapters 1-150 (will stop at API errors)
        chapters_to_fetch = list(range(1, 151))
        fetch_all = True
    elif '-' in chapter_input:
        try:
            start, end = map(int, chapter_input.split('-'))
            chapters_to_fetch = list(range(start, end + 1))
            fetch_all = False
        except ValueError:
            console.print("[red]Invalid chapter range format[/red]")
            return
    else:
        try:
            chapter_num = int(chapter_input)
            chapters_to_fetch = [chapter_num]
            fetch_all = False
        except ValueError:
            console.print("[red]Invalid chapter number[/red]")
            return
    
    # Ask for rate limit delay
    console.print("\n[bold yellow]⚠️  Rate Limiting[/bold yellow]")
    console.print("[dim]To respect the free API, add delay between requests[/dim]")
    console.print("[dim]Recommended: 1-2 seconds[/dim]")
    
    delay_input = input("Delay between requests (seconds) [default: 1.5]: ").strip()
    try:
        delay = float(delay_input) if delay_input else 1.5
        if delay < 0:
            delay = 1.5
    except ValueError:
        console.print("[yellow]Invalid delay, using default 1.5s[/yellow]")
        delay = 1.5
    
    # Confirm before fetching
    if not click.confirm(f"\nProceed with fetching {len(selected_books)} book(s) with {delay}s delay?", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Calculate estimated time
    total_chapters_to_try = len(selected_books) * len(chapters_to_fetch)
    estimated_time = (total_chapters_to_try * delay) / 60  # in minutes
    
    # Fetch each book's chapters
    console.print(f"\n[bold cyan]Fetching {len(selected_books)} book(s) with {delay}s delay between requests...[/bold cyan]")
    if estimated_time > 1:
        console.print(f"[dim]Estimated time: ~{estimated_time:.1f} minutes (for up to {total_chapters_to_try} chapters)[/dim]")
    else:
        console.print(f"[dim]Estimated time: ~{estimated_time * 60:.0f} seconds (for up to {total_chapters_to_try} chapters)[/dim]")
    console.print("[dim]This may take a while. Please be patient.[/dim]\n")
    
    success_count = 0
    fail_count = 0
    start_time = time.time()
    
    for book in selected_books:
        book_name = book['name']
        console.print(f"\n[bold cyan]Fetching: {book_name}[/bold cyan]")
        
        book_success = 0
        book_fail = 0
        
        for chapter in chapters_to_fetch:
            try:
                # Fetch chapter
                data = fetch_by_reference(book_name, str(chapter), None)
                
                if data:
                    # Auto-save each chapter
                    try:
                        with QueryDB() as db:
                            saved_id = db.save_query(data)
                        console.print(f"  [green]✓ {book_name} {chapter} (ID: {saved_id})[/green]")
                        book_success += 1
                    except Exception as e:
                        console.print(f"  [red]✗ Failed to save {book_name} {chapter}: {e}[/red]")
                        book_fail += 1
                else:
                    # If fetching 'all', stop at first failure (end of book)
                    if fetch_all:
                        console.print(f"  [dim]Reached end of {book_name} at chapter {chapter}[/dim]")
                        break
                    else:
                        console.print(f"  [red]✗ Failed to fetch {book_name} {chapter}[/red]")
                        book_fail += 1
                
                # Rate limiting: wait before next request (but not after last one)
                if chapter != chapters_to_fetch[-1] or book != selected_books[-1]:
                    time.sleep(delay)
                    
            except Exception as e:
                if fetch_all:
                    # Silently stop at first error when fetching all
                    break
                else:
                    console.print(f"  [red]✗ Error fetching {book_name} {chapter}: {e}[/red]")
                    book_fail += 1
                
                # Still wait on error (but shorter)
                if chapter != chapters_to_fetch[-1] or book != selected_books[-1]:
                    time.sleep(delay / 2)
        
        success_count += book_success
        fail_count += book_fail
        
        console.print(f"  [bold]{book_name}: {book_success} chapters saved[/bold]")
    
    # Summary
    elapsed_time = time.time() - start_time
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  [green]✓ Success: {success_count}[/green]")
    if fail_count > 0:
        console.print(f"  [red]✗ Failed: {fail_count}[/red]")
    
    if elapsed_time > 60:
        console.print(f"  [dim]Time elapsed: {elapsed_time / 60:.1f} minutes[/dim]")
    else:
        console.print(f"  [dim]Time elapsed: {elapsed_time:.1f} seconds[/dim]")
    
    input("\nPress Enter to continue...")
