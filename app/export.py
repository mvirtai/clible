"""
Export utilities for clible.

Formats verse data as Markdown and exports saved queries to files
under data/exports/.
"""

from pathlib import Path

import click
from loguru import logger

from app.db.queries import QueryDB
from app.ui import console

EXPORT_DIR = Path(__file__).resolve().parent.parent / "data" / "exports"


def format_verse_data_markdown(data: dict) -> str:
    """Format verse data as Markdown"""
    reference = data.get('reference', 'Unknown reference')
    translation_name = data.get('translation_name', 'Unknown translation')
    translation_id = data.get('translation_id', '')
    translation_note = data.get('translation_note', '')
    verses = data.get('verses', [])
    created_at = data.get('created_at', '')

    lines = []

    lines.append(f"# {reference}\n\n")

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

    current_chapter = None
    for verse in verses:
        chapter = verse.get('chapter')
        verse_num = verse.get('verse')
        text = verse.get('text', '').strip()

        if chapter != current_chapter:
            if current_chapter is not None:
                lines.append("\n")
            lines.append(f"## Chapter {chapter}\n\n")
            current_chapter = chapter

        lines.append(f"[**{verse_num}**] {text}\n\n")

    return "".join(lines)


def export_query_to_markdown(query_id: str, output_path: Path | None = None) -> Path | None:
    """
    Export a saved query to a Markdown file.

    Args:
        query_id: ID of the saved query to export
        output_path: Optional path for output file. If None, auto-generates filename.

    Returns:
        Path to exported file, or None if export failed
    """
    db = QueryDB()
    data = db.get_single_saved_query(query_id)

    if not data:
        logger.error(f"Query with ID '{query_id}' not found")
        return None

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        reference = data.get('reference', 'unknown').replace(' ', '_').replace(':', '-')
        filename = f"{reference}.md"
        output_path = EXPORT_DIR / filename
    else:
        if not output_path.is_absolute():
            output_path = EXPORT_DIR / output_path

    markdown_content = format_verse_data_markdown(data)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        logger.info(f"Exported query {query_id} to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to write markdown file: {e}")
        return None
