# clible

A command-line Bible study tool that fetches verses from [bible-api.com](https://bible-api.com/) and provides tools for saving, searching, and exporting Bible verses.

## Purpose

`clible` is designed to help you:
- Quickly fetch Bible verses, chapters, or random verses from the web
- Save your favorite verses and queries to a local database
- Search through your saved verses for specific words
- Export your saved verses to Markdown files for documentation or study notes

The application uses an interactive terminal menu system, making it easy to navigate and use without remembering command-line flags.

## Requirements

- Python 3.12 (matches `.python-version`)
- [uv](https://github.com/astral-sh/uv) for environment management

## Installation

1. Clone the repository
2. Install dependencies:

```bash
uv sync
```

This creates `.venv/`, installs the packages, and updates `uv.lock` so everyone shares the same dependency snapshot.

## Usage

### Starting the Application

Run the application with:

```bash
uv run python -m app.cli
```

This launches the interactive main menu.

### Main Menu Options

The application provides a terminal-based menu interface with the following options:

1. **Fetch from API** - Access the API menu to fetch verses
2. **Show all saved verses** - View all queries you've saved to the database
3. **Analytic tools** - Search and analyze your saved verses
4. **Exports menu** - Export saved verses to various formats

### Fetching Verses

From the "Fetch from API" menu, you can:

- **Fetch verse by reference**: Enter a book name, chapter, and verse(s) (e.g., `John`, `3`, `16` or `16-18`)
- **Fetch chapter by reference**: Enter a book name and chapter to fetch the entire chapter
- **Fetch random verse**: Get a random verse from the API

After fetching, you'll see the verses displayed in a formatted Rich panel with:
- Reference (e.g., "John 3:16")
- Translation information
- Verse numbers and text

You'll be prompted to save the result to your local database.

### Viewing Saved Verses

Select "Show all saved verses" from the main menu to see all your saved queries with:
- Query ID
- Reference
- Number of verses
- Timestamp when saved

### Analytics

The analytics menu currently provides:

- **Search word**: Search for a specific word across all your saved verses. Results show:
  - Total number of matches
  - Breakdown by book
  - Each matching verse with the word highlighted
  - Full reference for each match

### Exports

The exports menu allows you to:

- **Export verses to markdown**: Export any saved query to a Markdown file
  - Enter the query ID when prompted
  - Optionally specify a filename (or press Enter for auto-generated name)
  - Files are saved to `data/exports/` directory

## Features

### Database Storage

The application uses SQLite to store:
- **Queries**: Saved verse references with metadata
- **Books**: Bible book names
- **Verses**: Individual verse text and references
- **Translations**: Translation metadata (name, abbreviation, notes)

All data is stored locally in `app/db/clible.db`.

### Rich Terminal UI

The application uses the [Rich](https://github.com/Textualize/rich) library for beautiful terminal output:
- Formatted panels for verse display
- Color-coded information
- Clear menu navigation

## Development Direction

The application is being developed with a focus on:

1. **Terminal User Interface**: The application has moved away from command-line flags to a fully interactive menu system for better user experience
2. **Local Data Management**: Emphasis on saving and managing your personal collection of verses
3. **Search and Analytics**: Tools to help you find and analyze verses in your saved collection
4. **Export Capabilities**: Ability to export your saved verses for use in other tools or documentation

### Planned Features

- Word frequency analysis for saved verses
- Additional export formats (text, JSON)
- More analytics tools

## Project Structure

```
clible/
├── app/
│   ├── analytics/          # Analytics tools (word search, frequency analysis)
│   ├── db/                 # Database queries and SQLite connection
│   ├── menus/              # Menu system and navigation
│   ├── validations/        # Input validation
│   ├── api.py              # Bible API integration
│   ├── cli.py              # Main CLI entry point
│   ├── export.py           # Export functionality
│   └── utils.py            # Utility functions and formatting
├── data/
│   ├── exports/            # Exported Markdown files
│   └── mock_data.json      # Mock data for testing
└── tests/                  # Test suite
```

## Technical Details

- **API**: Fetches from `http://bible-api.com`
- **Database**: SQLite with relational schema (queries, books, verses, translations)
- **Logging**: Uses `loguru` for structured logging
- **Testing**: pytest for unit tests

## License

See project files for license information.
