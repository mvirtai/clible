# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Future enhancements – see README.

## [0.1.0] - 2026-01-24

Initial batch release. Bundles all features developed to date.

### Added

- **Core**
  - Verse fetching from [bible-api.com](https://bible-api.com/) (WEB, KJV, BBE, ASV, YLT, NIV)
  - SQLite local storage for queries and verses
  - Session management with named sessions and multi-user support
  - User management and authentication (#13)
  - AppState singleton for application-level state (#14, #15)
- **API & Fetching**
  - Fetch by reference, chapter, random verse (#9)
  - Book list fetching and multi-book fetch (#20)
  - Max chapter and verse calculation (#29)
  - Caching for max chapter/verse in API (#31)
  - Verse data cache: reuse saved queries and session cache before API calls (#33, see `docs/PR_VERSE_DATA_CACHE.md`)
  - API cache for chapters/verses (#33)
- **CLI & UI**
  - Click-based CLI with menu-driven interface
  - Item selection and improved user interaction (#19)
  - Status bar showing current user and session (#26)
  - Rich terminal UI (tables, panels, colors)
- **Analytics**
  - Word frequency analysis with stop-word filtering (#9)
  - Phrase analysis (bigrams, trigrams) (#10)
  - Word search across saved verses with context highlighting
  - Translation comparison (side-by-side, two translations) (#27)
  - Visualization options (plotext, matplotlib) (#21)
  - Analysis tracking and history (#21, #24)
  - Analysis history filtering by session (#25)
  - User name in analysis history (#24)
- **Session & Queries**
  - Save queries and link to active sessions (#22)
  - Multi-query support (e.g. `1, 2, 3-10`) (#23)
  - Session cache for temporary sessions
  - SessionManager enhancements and tests (#17, #18)
- **Export**
  - Markdown and plain text export to `data/exports/`
- **DevOps**
  - Dockerfile and Docker Compose (#32)
  - Docker credentials and CI workflows (#16)
  - Taskfile for Docker/tasks
  - Comprehensive test suite (pytest, mocked API/DB)

### Changed

- Refactored session management and CLI structure (#14, #15, #17, #18)
- Enhanced logging and error handling in caching (#34)
- Updated Taskfile and README for Docker and usage

### Fixed

- API rate limiting: 1 s pauses between API calls to avoid 419/429 (#30, #34)
- Translation comparison save prompt when fetch fails
- Session linking for temporary sessions (queries in cache)
- Range support for word frequency and phrase analysis
- Various syntax and typo fixes in analytics menu

### Removed

- Reading statistics option (removed for now; #11, #12)

---

For detailed PR descriptions, see the `docs/` directory (e.g. `PR_VERSE_DATA_CACHE.md`, `PR_SESSION_ANALYSIS_FIXES.md`, `PR_TRANSLATION_COMPARISON.md`).
