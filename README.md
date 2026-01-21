# clible

A command-line Bible study tool with advanced analytics, translation comparison, and session management capabilities. Fetches verses from [bible-api.com](https://bible-api.com/), stores them locally in SQLite, and provides powerful tools for verse analysis and export.

## Features

### Core Functionality
- **Fetch Bible Verses**: Retrieve verses, chapters, or random verses from Bible API
- **Multiple Translations**: Support for WEB, KJV, BBE, ASV, YLT, and NIV translations
- **Local Database**: Save queries to SQLite for offline access and analysis
- **Session Management**: Organize your Bible studies into named sessions
- **User Management**: Multi-user support with automatic authentication

### Analytics Tools
- **Word Search**: Search for specific words across all saved verses with context highlighting
- **Translation Comparison**: Side-by-side comparison of verses in two different translations
- **Word Frequency Analysis**: Analyze word usage patterns with stop word filtering
- **Phrase Analysis**: Discover common bigrams and trigrams in biblical text
- **Reading Statistics**: Track vocabulary size and text complexity metrics
- **Analysis History**: View and manage past analyses with full metadata tracking

### Export & Visualization
- **Markdown Export**: Export verses and queries to formatted Markdown files
- **Text Export**: Plain text export for maximum compatibility
- **Rich Terminal UI**: Beautiful terminal interface with colors, tables, and panels
- **Status Bar**: Real-time display of current user and active session

## Requirements

- **Python 3.12+** (matches `.python-version`)
- **[uv](https://github.com/astral-sh/uv)** for dependency management

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

This creates `.venv/`, installs all packages, and updates `uv.lock` to ensure consistent dependencies across environments.

## Usage

### Quick Start

Run the interactive CLI:

```bash
uv run python -m app.cli
```

Or if installed as a package:

```bash
clible
```

### Command-Line Options

```bash
clible [OPTIONS]
```

**Available options:**
- `--user`, `-u`: Username for session (default: "default")
- `--output`, `-o`: Output format - `text` or `json` (default: `text`)
- `--book`, `-b`: Bible book name (e.g., `John`)
- `--chapter`, `-c`: Chapter number
- `--verses`, `-v`: Verse number(s), e.g., `16` or `16-18`
- `--use-mock/--no-use-mock`, `-um/-UM`: Use mock data instead of API (default: `false`)

**Example:**

```bash
clible --user john --output text
```

### Main Menu Structure

The application provides five main menu sections:

1. **Fetch from API** - Retrieve verses from Bible API
   - Fetch verse by reference (e.g., John 3:16)
   - Fetch entire chapter
   - Fetch random verse
   - Fetch multiple books

2. **Show all saved verses** - Browse saved queries with metadata

3. **Analytic tools** - Comprehensive Bible analysis features
   - Search for words across verses
   - Compare translations side-by-side
   - Word frequency analysis
   - Phrase analysis (bigrams/trigrams)
   - Analyze current session
   - Analyze multiple queries
   - Analyze by book
   - View analysis history

4. **Exports menu** - Export data to various formats
   - Export verses to Markdown
   - Export verses to plain text

5. **Session management** - Organize Bible studies
   - Start new session
   - Resume existing session
   - List all sessions
   - Save session queries

## Key Features in Detail

### Translation Comparison

Compare the same verse(s) across two different Bible translations side-by-side:

1. Select book, chapter, and verses (or entire chapter)
2. Choose two translations from available options (WEB, KJV, BBE, ASV, YLT, NIV)
3. View verses displayed in a formatted table with verse numbers highlighted
4. Easily identify translation differences and nuances

**Supported Translations:**
- `web` - World English Bible (default, public domain)
- `kjv` - King James Version
- `bbe` - Bible in Basic English
- `asv` - American Standard Version
- `ylt` - Young's Literal Translation
- `niv` - New International Version (availability may vary)

### Session Management

Organize your Bible studies into logical sessions:

- **Create Sessions**: Start new study sessions with custom names and scopes
- **Query Organization**: Save fetched verses directly to active sessions
- **Session Cache**: Temporarily store queries before committing to database
- **Resume Studies**: Pick up where you left off with saved sessions
- **Multi-user Support**: Each user maintains their own sessions

### Analytics Features

#### Word Frequency Analysis
- Analyze word usage patterns in your saved verses
- Automatic stop word filtering (common words like "the", "and", "is")
- Vocabulary size calculation
- Type-token ratio for text complexity measurement
- Results can be saved to analysis history

#### Phrase Analysis
- **Bigrams**: Find most common two-word phrases
- **Trigrams**: Discover recurring three-word patterns
- Useful for identifying key themes and repeated concepts
- Filter by frequency threshold

#### Word Search
- Search across all saved verses for specific words
- Results grouped by book with chapter and verse references
- Context highlighting for search terms
- Case-insensitive matching

#### Analysis History
- All analyses automatically saved with metadata
- Track analysis type, scope, and timestamps
- Associate analyses with sessions and users
- View past analysis results at any time

### Saving Queries

After fetching verses, you'll be prompted to save the result. Saved queries include:

- Reference (e.g., "John 3:16-18")
- Translation information (name, abbreviation, notes)
- Complete verse text with chapter and verse numbers
- Timestamp of when saved
- Association with current session (if active)

### Export Capabilities

#### Markdown Export
- Automatically generated filenames from verse references
- Formatted with headers, translation information
- Verse numbers and chapter divisions preserved
- Saved to `data/exports/` directory

#### Text Export
- Plain text format for universal compatibility
- Clean formatting without markup
- Easy to share or import into other tools

## Project Structure

```text
clible/
├── app/
│   ├── analytics/          # Analytics modules
│   │   ├── analysis_tracker.py    # Analysis history tracking
│   │   ├── phrase_analysis.py     # Bigram/trigram analysis
│   │   ├── reading_stats.py       # Reading statistics
│   │   ├── translation_compare.py # Translation comparison
│   │   ├── visualizations.py      # Data visualization
│   │   └── word_frequency.py      # Word frequency analysis
│   ├── db/                 # Database layer
│   │   ├── queries.py      # SQLite operations
│   │   └── clible.db       # SQLite database (created on first run)
│   ├── menus/              # Menu system
│   │   ├── analytics_menu.py
│   │   ├── api_menu.py
│   │   ├── exports_menu.py
│   │   ├── history_menu.py
│   │   ├── session_menu.py
│   │   ├── menu_utils.py
│   │   └── menus.py        # Menu definitions
│   ├── validations/        # Input validation
│   │   ├── click_params.py
│   │   ├── validation_lists.py
│   │   └── validations.py
│   ├── api.py              # Bible API integration
│   ├── cli.py              # Main CLI entry point
│   ├── export.py           # Export functionality
│   ├── session_manager.py  # Session state management
│   ├── status_bar.py       # Status bar display
│   ├── ui.py               # UI utilities and Rich console
│   └── utils.py            # General utility functions
├── data/
│   ├── exports/            # Exported Markdown/text files
│   ├── mock_data.json      # Mock data for testing
│   └── stop_words.json     # Stop words for analytics
├── docs/                   # Project documentation
├── tests/                  # Test suite
├── pyproject.toml          # Project configuration
├── uv.lock                 # Dependency lock file
└── README.md
```

## Database Schema

The application uses SQLite with the following tables:

### Core Tables
- **translations**: Translation metadata (id, abbr, name, note)
- **books**: Bible book names (id, name)
- **users**: User accounts (id, name, created_at)

### Query Tables
- **queries**: Query metadata (id, reference, created_at, translation_id)
- **verses**: Verse data (id, query_id, book_id, chapter, verse, text, snippet)

### Session Tables
- **sessions**: Study sessions (id, user_id, name, scope, created_at, updated_at)
- **session_queries**: Links queries to sessions (session_id, query_id)
- **session_queries_cache**: Temporary query cache (id, session_id, reference, verse_data)

### Analysis Tables
- **analysis_history**: Analysis metadata (id, user_id, session_id, analysis_type, scope, timestamp)
- **analysis_results**: Analysis output data (id, analysis_id, result_type, result_data, chart_path)

The database file is created automatically at `app/db/clible.db` on first run with foreign key constraints enabled.

## Dependencies

- **click**: Command-line interface framework with parameter validation
- **rich**: Terminal formatting, tables, and UI components
- **loguru**: Advanced logging with automatic formatting
- **requests**: HTTP requests to Bible API
- **pytest**: Testing framework with fixtures and mocking
- **pytest-mock**: Mock/patch support for pytest
- **pytest-cov**: Code coverage reporting
- **plotext**: Terminal-based plotting
- **matplotlib**: Advanced data visualization
- **simple-term-menu**: Interactive terminal menus

## Development

### Running Tests

Run the entire test suite:

```bash
uv run pytest
```

Run with coverage report:

```bash
uv run pytest --cov=app --cov-report=term-missing
```

Run specific test file:

```bash
uv run pytest tests/test_translation_compare.py
```

### Code Style

The project follows these conventions:

- **PEP 8 style guidelines** for Python code
- **English for all code comments** regardless of variable/function names
- **Docstrings** for all modules, classes, and public functions
- **Type hints** for function parameters and return values
- **Descriptive names** for variables, functions, and classes

### Project Conventions

- **Constants**: UPPERCASE_WITH_UNDERSCORES
- **Functions/Methods**: lowercase_with_underscores
- **Classes**: PascalCase
- **Private methods**: _leading_underscore
- **Database IDs**: UUIDs for all primary keys
- **Timestamps**: ISO 8601 format via SQLite CURRENT_TIMESTAMP

## Testing

The project includes comprehensive test coverage:

- **API tests**: Mocked HTTP requests and response handling
- **Database tests**: Schema validation and CRUD operations
- **Analytics tests**: Word frequency, phrase analysis, translation comparison
- **Integration tests**: End-to-end menu and workflow testing
- **Validation tests**: Input validation and parameter type checking

All tests use fixtures and mocking to avoid external dependencies.

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Write tests** for new features and bug fixes
3. **Follow code style** conventions (PEP 8, English comments)
4. **Update documentation** including README and docstrings
5. **Run tests** to ensure nothing breaks
6. **Submit a pull request** with clear description

## Documentation

Detailed documentation is available in the `docs/` directory:

- PR descriptions for major features
- Analysis tracker logic and integration guides
- Session management documentation
- Status bar implementation details
- Refactoring descriptions and conventions

## Future Enhancements

Potential improvements for future releases:

- **Export Enhancements**: PDF export, comprehensive analytics export
- **Advanced Analytics**: Concordance generation, cross-reference analysis
- **Translation Features**: Compare 3+ translations, highlight common words
- **Visualization**: Charts for word frequency, reading statistics over time
- **Search Improvements**: Regex search, proximity search, phrase search
- **Import Features**: Import verses from files, other Bible software
- **Mobile Support**: REST API for mobile apps
- **Offline Mode**: Download translations for offline use

## License

[Add license information here]

## Acknowledgments

- Bible verses provided by [bible-api.com](https://bible-api.com/)
- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal UI
- Dependency management by [uv](https://github.com/astral-sh/uv)

## Support

For bug reports and feature requests, please open an issue on the project repository.

---

**Version**: 0.1.0  
**Python**: 3.12+  
**Status**: Active Development
