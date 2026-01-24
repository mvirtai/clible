# PR: Add User Name to Analysis History

## Summary

This PR adds user name display to the analysis history feature, allowing users to see who performed each analysis. It includes comprehensive database schema improvements, bug fixes, and extensive test coverage.

## Changes

### Database Schema (`app/db/queries.py`)

**New column in `analysis_history` table:**

- Added `user_name TEXT NOT NULL` column to store the user's name at the time of analysis
- This denormalizes the data intentionally for faster queries and historical accuracy (if username changes, history shows original name)
- Uses "Unknown" as default value when user_id is not available or invalid

**Schema reorganization:**

- Reorganized table creation into modular functions for better maintainability:
  - `_create_core_tables()` - translations, books, users (no dependencies)
  - `_create_query_tables()` - queries, verses (depend on translations, books)
  - `_create_session_tables()` - sessions, session_queries, session_queries_cache (depend on users, queries)
  - `_create_analysis_tables()` - analysis_history, analysis_results (depend on users, sessions)
- Added `_initialize_database()` method that coordinates table creation
- Added comprehensive schema documentation with dependency order in comments
- Fixed `_reset_database()` to:
  - Drop tables in correct order (child tables first) to avoid foreign key constraint errors
  - Recreate all tables after reset to ensure clean state

**Bug fix:**

- Fixed recursive call bug in `add_query_to_session()` where `db.add_query_to_session()` was called instead of `self.cur.execute()`
- Function now correctly uses `self.cur.execute()` and handles IntegrityError for duplicates gracefully

### Analysis Tracker (`app/analytics/analysis_tracker.py`)

**User name retrieval:**

- Modified `save_word_frequency_analysis()` to:
  - Fetch user name via `db.get_user_by_id(self.user_id)`
  - Include `user_name` in the INSERT statement
  - Use "Unknown" as default when user_id is None or user not found
- Modified `save_phrase_analysis()` with the same user name retrieval logic
- Both functions now handle edge cases (missing user_id, invalid user_id) gracefully

**Bug fix:**

- Fixed typo: `self.user.id` → `self.user_id` (AttributeError fix)

### History Menu (`app/menus/history_menu.py`)

**Display improvements:**

- Added "User" column to analysis history table display
- Shows `user_name` from the analysis record, with "N/A" fallback for legacy data
- Fixed typo: 'N/Aa' → 'N/A'

### User Queries (`app/db/queries.py`)

**Enhancements:**

- `get_user_by_id()` now properly documented and tested
- Returns None for invalid user IDs (no exceptions)

## Testing

### New Test Files

1. **`tests/test_analysis_tracker_user_name.py`** (8 tests)

   - Tests user_name storage in word frequency analysis
   - Tests user_name storage in phrase analysis
   - Tests user_name retrieval from history
   - Edge cases: missing user_id, invalid user_id, different users

2. **`tests/test_database_reset.py`** (5 tests)

   - Tests database reset drops all tables correctly
   - Tests tables are recreated after reset
   - Tests foreign key constraint handling
   - Tests schema preservation (including user_name column)

3. **`tests/test_session_queries.py`** (7 tests)
   - Tests `add_query_to_session()` bug fix
   - Tests query-session linking
   - Tests duplicate handling
   - Tests edge cases (None values, invalid IDs)

### Updated Test Files

- **`tests/test_analysis_tracker.py`** - Added user_name verification to existing tests
- **`tests/test_user_queries.py`** - Added `get_user_by_id()` tests

**Total: 26 new/updated tests, all passing**

## Database Migration Note

If you have existing data in `analysis_history` without `user_name`:

1. The column was added as `NOT NULL` - existing records will need migration
2. Option A: Reset database with `_reset_database()` (loses data) - **Recommended for development**
3. Option B: Run migration to add column with default value "Unknown", then update existing records

## Manual Testing Checklist

1. ✅ Create a new analysis (word frequency or phrase analysis)
2. ✅ Verify analysis is saved with user name in database
3. ✅ View analysis history - user name should appear in the table
4. ✅ Verify database reset works without foreign key errors
5. ✅ Test with multiple users - each analysis shows correct user name
6. ✅ Test without user_id - shows "Unknown" in history

## Files Changed

### Core Changes

- `app/db/queries.py` - Schema improvements, modular table creation, bug fixes
- `app/analytics/analysis_tracker.py` - User name storage, edge case handling, bug fix
- `app/menus/history_menu.py` - User name display, typo fix

### Test Files

- `tests/test_analysis_tracker_user_name.py` - **NEW** - User name functionality tests
- `tests/test_database_reset.py` - **NEW** - Database reset tests
- `tests/test_session_queries.py` - **NEW** - Session-query linking tests
- `tests/test_analysis_tracker.py` - Updated with user_name checks
- `tests/test_user_queries.py` - Added get_user_by_id tests

## Breaking Changes

None - This is a backward-compatible addition. Existing functionality remains unchanged.

## Notes

- User name is denormalized (stored in analysis_history) for performance and historical accuracy
- Foreign key constraints ensure data integrity
- All edge cases are handled gracefully with appropriate defaults
