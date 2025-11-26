# CLI usage guide

`clible` is a small command line helper that fetches verses from [bible-api.com](https://bible-api.com/) or from the bundled `app/data/mock_data.json`. These steps get you from checkout to a working shell experience.

## Requirements

- Python 3.12 (matches `.python-version`)
- [uv](https://github.com/astral-sh/uv) for environment management

## Install dependencies

```bash
uv sync
```

This creates `.venv/`, installs the packages, and updates `uv.lock` so everyone shares the same dependency snapshot.

## Running the CLI

### Interactive menu

```bash
uv run python -m app.cli
```

You’ll be prompted for book, chapter, and verses; output defaults to a Rich panel.

### Direct flags

```bash
uv run python -m app.cli \
  --book John \
  --chapter 3 \
  --verses 16 \
  --output text
```

## Available flags

- `--book` / `-b`: Bible book, e.g. `John`
- `--chapter` / `-c`: Chapter identifier (string to allow prefixes)
- `--verses` / `-v`: Verse or range, e.g. `16` or `16-18`
- `--output` / `-o`: `text` (Rich panel) or `json`
- `--use-mock` / `-um`: Load `app/data/mock_data.json` instead of calling the API

Providing all three location parameters skips the interactive menu. `--use-mock` alone defaults to John 3:16 for quick demos.
