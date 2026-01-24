# Conventions Audit (clible)

Summary of the codebase audit and changes applied to keep code and comments clear, sufficient, and consistent.

## Applied Changes

### 1. Cleanup

- **Removed** `app/menus/Untitled` – stray file (junk).
- **Fixed** `.cursorrules` typo: "Constantlly" → "Constantly".

### 2. Comments: English Only

Per `.cursorrules`, all comments must be in English.

- **tests/test_validations.py**: Finnish parametrize comments → English  
  (`Yksittäiset virheelliset` → "Single invalid inputs", etc.).
- **tests/test_fetch_by_reference.py**: Finnish inline comments → English  
  (HTTPError handling, mock setup).
- **tests/test_analysis_tracker.py**: Removed Finnish TODO `# ← LISÄÄ TÄMÄ!`.

### 3. Module-Level Docstrings

All app modules now have a short module docstring (English, 1–4 lines) describing purpose.

**Added docstrings to:**

- `app/api.py` – Bible API integration
- `app/db/queries.py` – SQLite layer, schema overview
- `app/cli.py` – CLI entry point and main menu
- `app/export.py` – Export to Markdown
- `app/state.py` – AppState singleton
- `app/status_bar.py` – Status bar component
- `app/menus/menus.py` – Menu definitions
- `app/menus/api_menu.py`, `exports_menu.py`, `history_menu.py`, `session_menu.py`, `menu_utils.py`, `analytics_menu.py`
- `app/validations/validations.py`, `validation_lists.py`
- `app/analytics/word_frequency.py`, `phrase_analysis.py`, `reading_stats.py` (stub)

**Already had module docstrings:**  
`translation_compare`, `click_params`, `analysis_tracker`, `visualizations`, `session_manager`, `ui`, `utils`.

### 4. Other Fixes

- **app/status_bar.py**: Class docstring "display" → "displays" (grammar).
- **app/validations/validation_lists.py**: `# old testament` / `# new testament` → `# Old Testament` / `# New Testament`.
- **app/analytics/word_frequency.py**: Removed redundant `# Minimal built-in stop word fallback...`; module docstring covers it.
- **app/export.py**: Removed `# Default export directory`; `EXPORT_DIR` is self-explanatory.
- **app/db/queries.py**: Replaced `# app/db/queries.py` with proper module docstring; kept schema block comment.

## Conventions (Reference)

### Naming

- **Constants**: `UPPERCASE_WITH_UNDERSCORES` (e.g. `MAIN_MENU`, `DEFAULT_STOP_WORDS`).
- **Functions / methods**: `lowercase_with_underscores`.
- **Classes**: `PascalCase`.
- **Private methods**: `_leading_underscore`.
- **Menus**: "Analytic tools" in UI; `run_analytic_menu` in code (matches menu label).  
  Folder `analytics/` is plural; both usages are intentional.

### Comments and Docstrings

- **Language**: English only (code, comments, docstrings).
- **Module docstrings**: Brief description of module role; 1–4 lines.
- **Functions / classes**: Docstrings for public API; explain "why" when non-obvious.
- **Inline comments**: Use sparingly; prefer clear names. Explain non-obvious logic.

### File Sizes (as of audit)

Largest modules:

- `app/db/queries.py` ~1000 lines – consider splitting (e.g. schema, CRUD, cache helpers) in future refactors.
- `app/menus/analytics_menu.py` ~640 lines – many options; could extract handlers.
- `app/api.py` ~400 lines, `app/analytics/analysis_tracker.py` ~400 lines – acceptable but watch growth.

### Documentation Layout

- **README.md**: User-facing overview, install, usage, structure.
- **CHANGELOG.md**: Version history (Keep a Changelog).
- **docs/**: PR descriptions, analysis tracker docs, conventions, audit (this file).

### Tests

- **Language**: Test names and comments in English.
- **Fixtures**: Use `db_path=temp_db` etc. for isolation; avoid leftover TODOs in Finnish.

## Recommendations

1. **Ruff (or similar)** – Add `ruff` (or another linter) to dev deps and CI for PEP 8 / import sorting.
2. **Docstring coverage** – Consider `interrogate` or `pydocstyle` to enforce docstrings on public API.
3. **Refactor large files** – When touching `queries.py` or `analytics_menu.py`, consider extracting helpers or submodules.
4. **SESSION_MANAGER_LOGIC.md** – Currently in `.gitignore`. If still relevant, move to `docs/` and track in git; otherwise remove from ignore or delete.

---

*Last audit: 2026-01-24. Re-run periodically and update this doc.*
