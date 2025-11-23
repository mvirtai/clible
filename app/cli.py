import json
import click

from app.api import fetch_verse_by_reference


@click.command()
@click.option('--book', '-b', prompt='Book', help='Bible book name (e.g. John)')
@click.option('--chapter', '-c', prompt='Chapter', help='Chapter number')
@click.option('--verses', '-v', prompt='Verse', help='Verse number(s), e.g. 1 or 1-6')
@click.option('--output', '-o', type=click.Choice(['json', 'text']), default='json', help='Output format')
def cli(book: str, chapter: str, verses: str, output: str):
    """
    CLI tool for fetching Bible verses from bible-api.com safely.
    """
    book = book.strip().lower()
    chapter = chapter.strip()
    verses = verses.strip()

    verse_data = fetch_verse_by_reference(book, chapter, verses)

    if verse_data:
        if output == 'json':
            click.echo(json.dumps(verse_data, indent=2))
        else:
            # Tekstimuotoinen output
            click.echo(f"\n{verse_data.get('reference', 'Unknown')}")
            click.echo(f"\n{verse_data.get('text', '').strip()}\n")
    else:
        click.echo("Failed to feth verse. Check logs for details.")
        raise click.Abort()
    

if __name__ == "__main__":
    cli()




# def get_ref_values() -> tuple[str, str, str]:
#     book = input("Book: ").strip().lower()
#     chapter = input("Chapter: ").strip()
#     verses = input("Verse(s): ").strip()
#     return book, chapter, verses


# def display_verse(verse_data: dict) -> None:
#     if verse_data:
#         print(json.dumps(verse_data, indent=2))
#     else:
#         print("Failed to fetch verse. Check logs for details.")
