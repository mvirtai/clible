# CLI Modularization Refactoring

## Overview

This PR refactors the CLI module by extracting menu handlers from the monolithic `cli.py` (1095 lines) into focused, maintainable modules following the existing `api_menu.py` pattern.

## Problem

The `cli.py` file had grown to 1095 lines with multiple responsibilities:

- Main entry point (~50 lines)
- Analytics menu handler (~476 lines) - largest section
- Exports menu handler (~30 lines)
- Session menu handler (~180 lines)
- History menu handler (~165 lines)
- Utility functions (~100 lines)

This made the code difficult to maintain, test, and navigate.

## Solution

Extracted each menu handler into its own dedicated module, following the established `api_menu.py` pattern:

### Files Created

1. **`app/menus/analytics_menu.py`** (~500 lines)

   - `run_analytic_menu()` - main analytics menu handler
   - `prompt_visualization_choice()` - visualization preferences prompt
   - Handles all 7 analytics menu options (word search, frequency analysis, phrase analysis, session analysis, multi-query analysis, book analysis, history)

2. **`app/menus/exports_menu.py`** (~60 lines)

   - `run_exports_menu()` - exports menu handler
   - `handle_export()` - export workflow function

3. **`app/menus/session_menu.py`** (~200 lines)

   - `run_session_menu()` - session management menu handler
   - Handles all 7 session operations (start, resume, end, save, list, delete, clear cache)

4. **`app/menus/history_menu.py`** (~180 lines)
   - `run_history_menu()` - analysis history viewer
   - Handles viewing, filtering, and displaying analysis history

### Files Modified

1. **`app/menus/menu_utils.py`** (extended)

   - Added `select_from_list()` - generic item selection utility
   - Added `parse_selection_range()` - range parsing for multi-select operations
   - Already contained `prompt_menu_choice()` and `render_menu()`

2. **`app/cli.py`** (simplified from 1095 to ~70 lines)
   - Now only contains:
     - Main entry point (`run_main_menu()`)
     - Click command definition (`@click.command()`)
     - Imports for menu handlers

## Benefits

- **Maintainability**: Each menu is self-contained in its own file, making it easier to locate and modify code
- **Readability**: Smaller, focused files are easier to understand at a glance
- **Testability**: Menu handlers can be tested independently without loading the entire CLI module
- **Consistency**: Follows the existing `api_menu.py` pattern, creating a uniform codebase structure
- **Reduced Duplication**: Common utilities are shared via `menu_utils.py` instead of being duplicated

## File Size Changes

```
Before:
app/cli.py: 1095 lines

After:
app/cli.py:                    ~70 lines (94% reduction)
app/menus/menu_utils.py:       extended (shared utilities)
app/menus/analytics_menu.py:   ~500 lines (NEW)
app/menus/exports_menu.py:     ~60 lines (NEW)
app/menus/session_menu.py:     ~200 lines (NEW)
app/menus/history_menu.py:     ~180 lines (NEW)
```

## Testing

- All existing functionality preserved - no breaking changes
- Menu handlers maintain the same function signatures
- All imports updated to reflect new module structure
- Linter checks pass with no errors

## Migration Notes

No migration needed - this is a pure refactoring with no API changes. All function signatures remain the same, only the code organization has changed.

## Related

This refactoring improves the codebase structure and sets a foundation for:

- Easier addition of new menu handlers
- More focused unit testing
- Better code organization for future features

---

**Note**: This refactoring is part of the `feat/improve-multi-querying` branch but is a standalone improvement that enhances code quality without changing functionality.
