from pathlib import Path
import click
from loguru import logger

from app.db.queries import QueryDB
from app.ui import console

# Default export directory
EXPORT_DIR = Path(__file__).resolve().parent.parent / "data" / "exports"

def format_verse_data_markdown(data: dict) -> str:
    """Format verse data as Markdown"""
    reference = data.get('reference', 'Unknown reference')
    translation_name = data.get('translation_name', 'Unknown translation')
    translation_id = data.get('translation_id', '')
    translation_note = data.get('translation_note', '')
    verses = data.get('verses', [])
    created_at = data.get('created_at', '')

    # Build markdown content
    lines = []

    # Header
    lines.append(f"# {reference}\n\n")

    # Translation info
    if translation_name:
        lines.append(f"**Translation:** {translation_name}")
        if translation_id:
            lines[-1] += f" {translation_id}"
        lines[-1] += "\n"
    
    if translation_note:
        lines.append(f"*{translation_note}*\n")
    
    if created_at:
        lines.append(f"**Saved**: {created_at}\n")
    

    lines.append("\n---\n\n")

    # Verses
    current_chapter = None
    for verse in verses:
        chapter = verse.get('chapter')
        verse_num = verse.get('verse')
        text = verse.get('text', '').strip()

        # Add chapter header if chapter changes
        if chapter != current_chapter:
            if current_chapter is not None:
                lines.append("\n")
            lines.append(f"## Chapter {chapter}\n\n")
            current_chapter = chapter
        
        # Format verse
        lines.append(f"[**{verse_num}**] {text}\n\n")
    
    return "".join(lines)


def export_query_to_markdown(query_id: str, output_path: Path | None = None) -> Path | None:
    db = QueryDB()
    data = db.get_single_saved_query(query_id)

    if not data:
        logger.error(f"Query with ID '{query_id}' not found")
        return None
    
    # Ensure export dir exists
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate filename if not provided
    if output_path is None:
        reference = data.get('reference', 'unknown').replace(' ', '_').replace(':', '-')
        filename = f"{reference}.md"
        output_path = EXPORT_DIR / filename
    else:
        # If relative path provided, use export directory
        if not output_path.is_absolute():
            output_path = EXPORT_DIR / output_path
    
    # Format and write markdown
    markdown_content = format_verse_data_markdown(data)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        logger.info(f"Exported query {query_id} to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to write markdown file: {e}")
        return None


# if __name__ == "__main__":
#     # FOR TESTING PURPOSES ONLY
#     db = QueryDB()
#     all_saved_verses = db.show_all_saved_queries()

#     if not all_saved_verses:
#         console.print("[dim]No saved queries found.[/dim]")
#     else:
#         console.print("\n[bold]Saved queries:[/bold]")
#         for verse in all_saved_verses:
#             console.print(f"  ID: {verse['id']} | Reference: {verse['reference']} | Verses: {verse['verse_count']}")
        
#         query_id = input("\nGive ID: ").strip()
#         if query_id:
#             output_file = input(f"Output file (press Enter for auto-generated name, will be saved to {EXPORT_DIR}): ").strip()
#             output_path = Path(output_file) if output_file else None
            
#             # Test export_query_to_markdown function
#             result = export_query_to_markdown(query_id, output_path)
            
#             if result:
#                 console.print(f"\n[bold green]✓ Successfully exported to: {result}[/bold green]")
#             else:
#                 console.print(f"\n[red]✗ Failed to export query with ID '{query_id}'[/red]")