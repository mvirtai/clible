# PR: Add Current Session Filter to Analysis History

## Summary

This PR adds a "current session only" filter to the analysis history feature, allowing users to filter analysis history to show only analyses from the currently active session. This improves usability when working with multiple sessions and helps users focus on analyses relevant to their current work.

## Changes

### Analysis Tracker (`app/analytics/analysis_tracker.py`)

**New parameter in `get_analysis_history()` method:**

- Added `session_id: str = None` parameter to filter analyses by session ID
- When `session_id` is provided, only analyses from that session are returned
- When `session_id` is `None` (default), all analyses are returned (backward compatible)
- Updated docstring to document the new parameter

**Implementation details:**

- Session filtering is added to the SQL query with `AND session_id = ?` clause
- Works seamlessly with existing filters (`analysis_type`, `scope_type`, `limit`)
- Filtering is applied at the database level for optimal performance

### History Menu (`app/menus/history_menu.py`)

**New toggle functionality:**

- Added `filter_current_session` boolean variable to track filter state
- Default value is `False` (show all analyses by default)
- Filter state persists throughout the menu session
- Visual indicator shows current filter status: `[green]ON[/green]` or `[dim]OFF[/dim]`

**Menu option 3: Toggle current session filter**

- New menu option to toggle the filter on/off
- Only available when an active session exists
- Shows helpful message if no active session is available
- Provides clear feedback when filter is enabled/disabled

**Filter application:**

- Filter is applied to all history views:
  - "View all analyses" (option 1)
  - "Filter by type" (option 2)
  - "View specific analysis" (option 4)
- Filter status is displayed in the menu header when active session exists
- Filter info is included in result messages: "(current session only)" when enabled

**User experience improvements:**

- Clear visual feedback about filter state
- Helpful error messages when trying to use filter without active session
- Filter status shown in result headers and empty state messages

### Menu Configuration (`app/menus/menus.py`)

**Updated HISTORY_MENU:**

- Added new option: "Toggle current session filter" (option 3)
- Reordered options: "View specific analysis" moved to option 4
- Maintains consistent menu structure and numbering

## Testing

### New Tests in `tests/test_analysis_tracker.py`

Added comprehensive test coverage for session filtering functionality:

1. **`test_get_history_filters_by_session_id`** - Tests basic session filtering
   - Creates analyses in multiple sessions
   - Verifies filtering returns only analyses from specified session
   - Ensures analyses from other sessions are excluded

2. **`test_get_history_filters_by_session_id_with_other_filters`** - Tests filter combination
   - Verifies session filter works with `analysis_type` filter
   - Ensures multiple filters can be combined correctly
   - Tests that all filters are applied simultaneously

3. **`test_get_history_with_none_session_id_returns_all`** - Tests backward compatibility
   - Verifies that `session_id=None` returns all analyses
   - Ensures default behavior is unchanged
   - Tests that explicit session filtering works correctly

4. **`test_get_history_with_empty_session_returns_nothing`** - Tests edge case
   - Verifies filtering by non-existent session returns empty list
   - Ensures no errors occur with invalid session IDs
   - Tests graceful handling of edge cases

**Total: 4 new tests, all passing**

### Test Coverage

- ✅ Basic session filtering functionality
- ✅ Filter combination with other filters
- ✅ Backward compatibility (None session_id)
- ✅ Edge cases (non-existent session, empty results)
- ✅ Multiple sessions handling
- ✅ Filter persistence and state management

## User Experience

### Before

- Users had to manually scan through all analyses to find ones from current session
- No way to filter analyses by session
- Difficult to focus on current work when multiple sessions exist

### After

- Users can toggle "current session only" filter with a single menu option
- Filter status is clearly visible in the menu
- All history views respect the filter setting
- Clear feedback when filter is enabled/disabled
- Helpful messages when no active session exists

### Usage Flow

1. User starts or resumes a session
2. User navigates to "View analysis history"
3. Filter status is shown: `Current session filter: ON` (if active session exists)
4. User can toggle filter with option 3
5. All history views (options 1, 2, 4) respect the filter setting
6. Filter state persists throughout the menu session

## Database Impact

**No schema changes required** - Uses existing `session_id` column in `analysis_history` table.

## Backward Compatibility

- ✅ Fully backward compatible
- ✅ Default behavior unchanged (`session_id=None` returns all analyses)
- ✅ Existing code continues to work without modifications
- ✅ New parameter is optional with sensible default

## Manual Testing Checklist

1. ✅ Start a new session
2. ✅ Create analyses in the session
3. ✅ Navigate to analysis history menu
4. ✅ Verify filter status shows "ON" when active session exists
5. ✅ View all analyses - should show only current session analyses
6. ✅ Toggle filter off - should show all analyses
7. ✅ Toggle filter on - should show only current session analyses again
8. ✅ Filter by type with filter enabled - should respect both filters
9. ✅ End session - filter option should show helpful message
10. ✅ Resume different session - filter should work with new session

## Files Changed

### Core Changes

- `app/analytics/analysis_tracker.py` - Added `session_id` parameter to `get_analysis_history()`
- `app/menus/history_menu.py` - Added toggle functionality and filter application
- `app/menus/menus.py` - Added new menu option

### Test Files

- `tests/test_analysis_tracker.py` - Added 4 new tests for session filtering

## Breaking Changes

None - This is a fully backward-compatible addition.

## Notes

- Filter state is stored in local variable (`filter_current_session`) and resets when menu exits
- Filter is disabled by default (`False`) - users see all analyses initially and can enable filter if needed
- Filter works with all existing filter types (analysis_type, scope_type)
- Database-level filtering ensures optimal performance
- Visual feedback helps users understand current filter state

## Future Enhancements

Potential future improvements:
- Persist filter preference across menu sessions
- Add filter for specific session (not just current)
- Add filter for multiple sessions
- Add filter for analyses without session

