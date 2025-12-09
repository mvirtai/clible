# clible

A command-line tool for Bible studies that fetches verses from [bible-api.com](https://bible-api.com/), saves them to a local database, and provides analytics and export capabilities.

## Features

- **Fetch Bible Verses**: Retrieve verses, chapters, or random verses from the Bible API
- **Save Queries**: Store fetched verses in a local SQLite database for later reference
- **View Saved Queries**: Browse all previously saved queries with metadata
- **Word Search**: Search for specific words across all saved verses
- **Export to Markdown**: Export saved queries to formatted Markdown files
- **Analytics Tools**: Analyze word frequency in saved verses (in development)
- **Interactive Menu System**: User-friendly terminal interface with Rich formatting
- **Mock Data Support**: Test the application using bundled mock data

## Requirements

- Python 3.12+ (matches `.python-version`)
- [uv](https://github.com/astral-sh/uv) for environment management

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd clible
```

2. Install dependencies:

```bash
uv sync
```

This creates `.venv/`, installs all packages, and updates `uv.lock` so everyone shares the same dependency snapshot.

## Usage

### Interactive Menu

Run the CLI with the interactive menu:

```bash
uv run python -m app.cli
```

The main menu provides access to:

1. **Fetch from API** - Fetch verses, chapters, or random verses
2. **Show all saved verses** - View all saved queries
3. **Analytic tools** - Search for words in saved verses
4. **Exports menu** - Export saved queries to Markdown

### Command-Line Flags

Currently, only the `--output` flag is functional:

```bash
uv run python -m app.cli --output text
```

**Available flags:**

- `--output` / `-o`: Output format - `text` (Rich panel) or `json` (default: `text`)

**Note:** The following flags are defined but not currently implemented:
- `--book` / `-b`: Bible book name (e.g., `John`)
- `--chapter` / `-c`: Chapter number
- `--verses` / `-v`: Verse number(s), e.g., `16` or `16-18`
- `--use-mock` / `-um`: Load verses from `app/data/mock_data.json` instead of calling the API

### Using the CLI Script

If installed as a package, you can also use:

```bash
clible
```

## Main Features

### Fetching Verses

The application supports three ways to fetch verses:

1. **By Reference**: Fetch specific verses (e.g., John 3:16 or John 3:16-18)
2. **By Chapter**: Fetch an entire chapter (e.g., John 3)
3. **Random Verse**: Fetch a random verse from the Bible

All fetched verses can be saved to the local database for later use.

### Saving Queries

After fetching verses, you'll be prompted to save the result. Saved queries include:

- Reference (e.g., "John 3:16")
- Translation information (name, abbreviation, notes)
- All verse text
- Timestamp of when it was saved

### Word Search

Search for specific words across all saved verses. The search:

- Finds all occurrences of the word (case-insensitive)
- Groups results by book
- Highlights the search word in the results
- Shows book, chapter, verse, and text for each match

### Export to Markdown

Export any saved query to a formatted Markdown file:

- Automatically generates filename from reference
- Includes translation information
- Formats verses with chapter headers
- Saves to `data/exports/` directory

## Project Structure

```text
clible/
├── app/
│   ├── __init__.py
│   ├── cli.py              # Main CLI entry point
│   ├── api.py              # Bible API integration
│   ├── export.py           # Markdown export functionality
│   ├── utils.py            # Utility functions for rendering
│   ├── analytics/          # Analytics tools
│   │   └── word_frequency.py
│   ├── db/                 # Database operations
│   │   ├── __init__.py
│   │   └── queries.py      # SQLite database queries
│   ├── menus/              # Menu system
│   │   ├── api_menu.py
│   │   ├── menu_utils.py
│   │   └── menus.py
│   └── validations/        # Input validation
│       ├── click_params.py
│       ├── validation_lists.py
│       └── validations.py
├── data/
│   ├── mock_data.json      # Mock data for testing
│   └── exports/            # Exported Markdown files
├── tests/                  # Test suite
├── pyproject.toml          # Project configuration
├── uv.lock                 # Dependency lock file
└── README.md
```

## Database Schema

The application uses SQLite with the following tables:

- **queries**: Stores query metadata (id, reference, created_at, translation_id)
- **books**: Stores book names (id, name)
- **verses**: Stores verse data (id, query_id, book_id, chapter, verse, text, snippet)
- **translations**: Stores translation information (id, abbr, name, note)

The database file is created automatically at `app/db/clible.db` on first run.

## Dependencies

- **click**: Command-line interface framework
- **rich**: Terminal formatting and UI
- **loguru**: Logging
- **requests**: HTTP requests to Bible API
- **pytest**: Testing framework

## Development

### Running Tests

```bash
uv run pytest
```

### Code Style

The project follows PEP 8 style guidelines. All code comments must be written in English.

## License

[Add license information here]

## Contributing

[Add contributing guidelines here]
