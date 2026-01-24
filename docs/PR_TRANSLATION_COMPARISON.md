# PR: Translation Comparison Feature

## Summary

This PR adds a translation comparison feature that allows users to compare the same Bible verse(s) side-by-side in two different translations. This enables users to study how different translations interpret the same biblical text, making it easier to understand nuances and differences between translations.

## Changes

### API Module (`app/api.py`)

**New parameter in `fetch_by_reference()` function:**

- Added `translation: str | None = None` parameter to specify which Bible translation to fetch
- When `translation` is provided, appends `?translation={translation}` to the API URL
- Defaults to `"web"` (World English Bible) when not specified
- Supports all bible-api.com translation identifiers (web, kjv, bbe, asv, ylt, niv, etc.)
- Backward compatible: existing calls without translation parameter work as before

**Implementation details:**

- Translation parameter is normalized to lowercase: `translation.lower() if translation else "web"`
- Applied to all fetch modes: single verse, verse range, chapter, and random verse
- Translation identifier is added to URL as query parameter: `?translation=kjv`
- Error handling remains the same (returns None on failure)

### Translation Comparison Module (`app/analytics/translation_compare.py`)

**New module for translation comparison functionality:**

**`AVAILABLE_TRANSLATIONS` constant:**

- List of supported translation identifiers: web, kjv, bbe, asv, ylt, niv
- Used for validation and user selection in menus
- Can be easily extended with additional translations

**`fetch_verse_comparison()` function:**

- Fetches the same verse(s) from two different translations
- Parameters: `book`, `chapter`, `verses` (optional), `translation1`, `translation2`
- Returns structured dictionary with:
  - `reference`: Verse reference string
  - `translation1`: Dict with translation1 data (verses, translation_name, translation_id)
  - `translation2`: Dict with translation2 data (same structure)
- Handles multiple verses: if verse range is specified (e.g., "16-18"), all verses are fetched
- Returns `None` if either fetch fails, with appropriate error logging

**`render_side_by_side_comparison()` function:**

- Displays verses in a Rich table format with two columns (one per translation)
- Each verse is shown on its own row with verse number and text
- Handles cases where translations have different numbers of verses
- Uses color coding: green for translation1, blue for translation2
- Displays verse numbers in bold for easy reference
- Shows "No verse" for missing verses when counts differ

**Features:**

- Supports verse ranges: multiple verses are displayed in separate rows
- Graceful error handling: shows appropriate messages for empty or invalid data
- Rich formatting: uses colored borders, headers, and verse numbering
- Spacing utilities: proper spacing before and after display

### Analytics Menu (`app/menus/analytics_menu.py`)

**New menu option: "Translation comparison" (option 2):**

- Added after "Search word" option, before analysis tools
- Integrated user-friendly workflow:
  1. Shows available books list
  2. Prompts for book, chapter, and verses (optional)
  3. Displays available translations for selection
  4. Allows user to select two translations by number or name
  5. Fetches and displays comparison

**Implementation details:**

- Uses `click.prompt()` for input validation (BookParam, ChapterParam, VersesParam)
- Translation selection accepts both numbers (1-6) and translation names (web, kjv, etc.)
- Fallback to defaults: web and kjv if invalid selections
- Shows first 6 translations in numbered list for easy selection
- Displays helpful error messages if fetch fails

**Updated menu structure:**

- All existing menu options renumbered (shifted by +1)
- "Translation comparison" is now option 2
- Word frequency analysis moved to option 4
- Phrase analysis moved to option 5
- Other options shifted accordingly (3→4, 4→5, 5→6, 6→7, 7→8)

### Menu Configuration (`app/menus/menus.py`)

**Updated ANALYTICS_MENU:**

- Added "Translation comparison" option after "Search word"
- Added separator line ("--------------------------------") to visually group comparison and analysis tools
- Maintains consistent menu structure and numbering

## Testing

### New Test File: `tests/test_translation_compare.py`

**5 comprehensive tests, all passing:**

1. **`test_fetch_verse_comparison`** - Basic functionality test

   - Verifies correct structure of returned dictionary
   - Tests translation name and ID are correctly preserved
   - Ensures verses are correctly included in both translations
   - Verifies verse numbers match expected values

2. **`test_fetch_verse_comparison_multiple_verses`** - Verse range handling

   - Tests fetching verse ranges (e.g., "16-18")
   - Verifies all verses in range are included
   - Ensures correct verse numbering across range
   - Tests both translations handle multiple verses correctly

3. **`test_fetch_verse_comparison_failure`** - Error handling

   - Tests behavior when first API call fails (returns None)
   - Tests behavior when second API call fails
   - Verifies function returns None on any failure
   - Ensures no exceptions are raised on API errors

4. **`test_render_side_by_side_comparison`** - Rendering functionality

   - Tests table rendering with valid comparison data
   - Verifies rendering handles empty data gracefully
   - Tests rendering with None input (no crashes)
   - Ensures no exceptions are raised during rendering

5. **`test_render_side_by_side_comparison_multiple_verses`** - Multi-verse rendering
   - Tests rendering of multiple verses in side-by-side format
   - Verifies each verse appears on its own row
   - Ensures verse numbers are displayed correctly
   - Tests formatting consistency across multiple verses

**Test Coverage:**

- ✅ Basic fetch and comparison functionality
- ✅ Multiple verse handling (ranges)
- ✅ Error handling (API failures)
- ✅ Rendering with various data formats
- ✅ Edge cases (empty data, None values, missing verses)
- ✅ Data structure validation

**All tests use mocking:**

- API calls are mocked to avoid external dependencies
- Tests are fast and reliable
- No actual network requests during testing

### Updated Tests: `tests/test_fetch_by_reference.py`

**Test updates for backward compatibility:**

- Updated `test_fetch_by_reference_builds_correct_url` to expect `?translation=web` in URLs (default behavior)
- Added `test_fetch_by_reference_with_translation_parameter` to verify explicit translation parameter works correctly
- All existing tests continue to pass
- **Total: 1 new test, 2 updated tests, all passing**

## User Experience

### Before

- Users could only view one translation at a time
- Comparing translations required manually fetching verses twice
- No easy way to see differences between translations
- Difficult to study translation nuances

### After

- Users can compare two translations side-by-side in a single view
- Simple menu-driven workflow for translation selection
- Visual side-by-side layout makes differences immediately apparent
- Each verse displayed separately for clear comparison
- Verse numbers highlighted for easy reference

### Usage Flow

1. User navigates to "Analytic tools" → "Translation comparison"
2. User selects book, chapter, and verses (or entire chapter)
3. System displays available translations
4. User selects two translations (by number or name)
5. System fetches verses from both translations
6. Verses are displayed side-by-side in a formatted table
7. User can easily compare wording, phrasing, and nuances

### Example Output

```
┌─────────────────────────────────────┬─────────────────────────────────────┐
│          John 3:16                  │                                     │
├─────────────────────────────────────┼─────────────────────────────────────┤
│ [16] For God so loved the world...  │ [16] For God so loved the world...  │
│     (World English Bible)           │     (King James Version)            │
└─────────────────────────────────────┴─────────────────────────────────────┘
```

## Database Impact

**No database changes required** - This feature uses only API calls and in-memory data structures.

## Backward Compatibility

- ✅ Fully backward compatible
- ✅ Existing API calls without translation parameter work unchanged (defaults to "web")
- ✅ Existing menu options continue to work (just renumbered)
- ✅ No breaking changes to any existing functionality
- ✅ All existing tests continue to pass

## Manual Testing Checklist

1. ✅ Navigate to Analytics menu → Translation comparison
2. ✅ Select book, chapter, and verses
3. ✅ Select two different translations
4. ✅ Verify side-by-side display shows both translations
5. ✅ Test with single verse (e.g., John 3:16)
6. ✅ Test with verse range (e.g., John 3:16-18)
7. ✅ Test with entire chapter (no verses specified)
8. ✅ Verify verse numbers are displayed correctly
9. ✅ Test translation selection by number (1, 2, etc.)
10. ✅ Test translation selection by name (web, kjv, etc.)
11. ✅ Verify error handling when API fails
12. ✅ Test with different translation combinations

## Files Changed

### Core Changes

- `app/api.py` - Added `translation` parameter to `fetch_by_reference()`
- `app/analytics/translation_compare.py` - **NEW** - Translation comparison module
- `app/menus/analytics_menu.py` - Added translation comparison menu option
- `app/menus/menus.py` - Updated ANALYTICS_MENU structure

### Test Files

- `tests/test_translation_compare.py` - **NEW** - Comprehensive test suite (5 tests)
- `tests/test_fetch_by_reference.py` - **UPDATED** - Added translation parameter test, updated URL expectations (1 new test, 2 updated)

## Breaking Changes

None - This is a fully backward-compatible addition.

## Notes

### Design Decisions

1. **Side-by-side display over diff**: Traditional diff algorithms don't work well for Bible translations because they express the same meaning with different wording and sentence structures. Side-by-side comparison allows users to see both versions clearly.

2. **Two translations limit**: Initial implementation supports two translations to keep the interface clean. Future enhancements could support more translations or different display formats.

3. **Verse-level granularity**: Each verse is displayed separately, making it easy to compare specific verses. This works well for both single verses and verse ranges.

4. **Rich table format**: Uses Rich library's Table for professional terminal formatting with colors and borders, consistent with the rest of the application.

5. **Error handling**: Failures are handled gracefully with clear error messages, ensuring the application doesn't crash on API errors.

### Future Enhancements

Potential improvements for future PRs:

- Highlight common words between translations (vaihe 2)
- Support for more than two translations simultaneously
- Word-level diff highlighting (advanced)
- Save comparison results to analysis history
- Export comparisons to Markdown or PDF
- Compare translations from saved queries (not just API)
- Translation statistics (commonality, differences, etc.)

### API Translation Support

Currently supported translations from bible-api.com:

- `web` - World English Bible (default, public domain)
- `kjv` - King James Version
- `bbe` - Bible in Basic English
- `asv` - American Standard Version
- `ylt` - Young's Literal Translation
- `niv` - New International Version (availability may vary)

More translations can be added to `AVAILABLE_TRANSLATIONS` list as bible-api.com supports them.
