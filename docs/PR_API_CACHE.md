# PR Story: API Cache for Max Chapters and Max Verses

## Overview

This PR implements a caching mechanism for maximum chapter and verse calculations to improve performance and reduce API calls to `bible-api.com`. The cache stores previously calculated values in the database, eliminating the need for repeated API calls when the same information is requested.

## Problem Statement

Previously, `calculate_max_chapter()` and `calculate_max_verse()` functions made API calls every time they were invoked, even for the same book/chapter/translation combinations. This resulted in:

- **Performance issues**: Multiple API calls with 1-second delays between requests
- **Rate limiting**: Increased risk of 429 (Too Many Requests) errors
- **Unnecessary network traffic**: Repeated requests for static data (max chapters/verses don't change)
- **Poor user experience**: Slower response times when fetching verses with "all" chapters or verses

## Solution

Implemented a database-backed cache system that:

1. **Stores calculated values**: Max chapters and verses are cached in SQLite database tables
2. **Checks cache first**: Functions check cache before making API calls
3. **Updates cache automatically**: Newly calculated values are automatically cached for future use
4. **Handles failures gracefully**: Cache failures don't break functionality - functions fall back to API calls

## Database Schema Changes

### New Tables

**`book_chapter_cache`** table:

- `book_name` (TEXT NOT NULL) - Name of the book
- `translation` (TEXT NOT NULL) - Translation identifier (e.g., "web", "kjv")
- `max_chapter` (INTEGER NOT NULL) - Maximum chapter number
- `last_updated` (TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP) - When the cache was last updated
- PRIMARY KEY: `(book_name, translation)`

**`book_verse_cache`** table:

- `book_name` (TEXT NOT NULL) - Name of the book
- `chapter` (INTEGER NOT NULL) - Chapter number
- `translation` (TEXT NOT NULL) - Translation identifier
- `max_verse` (INTEGER NOT NULL) - Maximum verse number
- `last_updated` (TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP) - When the cache was last updated
- PRIMARY KEY: `(book_name, chapter, translation)`

## Implementation Details

### Database Layer (`app/db/queries.py`)

Added four new methods to `QueryDB` class:

1. **`get_cached_max_chapter(book_name, translation)`**
   - Retrieves cached max chapter for a book and translation
   - Returns `int | None`

2. **`set_cached_max_chapter(book_name, translation, max_chapter)`**
   - Stores or updates cached max chapter
   - Uses `INSERT OR REPLACE` to handle updates

3. **`get_cached_max_verse(book_name, chapter, translation)`**
   - Retrieves cached max verse for a book, chapter, and translation
   - Returns `int | None`

4. **`set_cached_max_verse(book_name, chapter, translation, max_verse)`**
   - Stores or updates cached max verse
   - Uses `INSERT OR REPLACE` to handle updates

### API Layer (`app/api.py`)

Modified two functions to use cache:

1. **`calculate_max_chapter(book, translation)`**
   - Checks cache before making API calls
   - Returns cached value immediately if available
   - Caches calculated value after successful API calculation
   - Handles cache failures gracefully (falls back to API)
   - Uses lazy import of `QueryDB` to avoid circular import issues

2. **`calculate_max_verse(book, chapter, translation)`**
   - Checks cache before making API calls
   - Returns cached value immediately if available
   - Caches calculated value after successful API calculation
   - Handles cache failures gracefully (falls back to API)
   - Uses lazy import of `QueryDB` to avoid circular import issues

**Note on Circular Import Prevention**:
The `QueryDB` class is imported inside the functions (lazy import) rather than at module level to prevent circular import issues. The import chain `app.api` → `app.db.queries` → `app.ui` → `app.api` would create a circular dependency if `QueryDB` were imported at module level. By importing it only when needed inside the functions, the circular dependency is broken.

### Error Handling

Both functions include try-except blocks around cache operations:

- Cache read failures: Logged as warnings, function continues with API call
- Cache write failures: Logged as warnings, function still returns calculated value
- Database errors don't break functionality
- Import errors (if `QueryDB` cannot be imported): Logged as warnings, function falls back to API calls

## Benefits

1. **Performance Improvement**
   - First request: Same speed as before (API call + cache write)
   - Subsequent requests: Instant response from cache (no API calls)
   - Eliminates multiple 1-second delays for repeated queries

2. **Reduced API Load**
   - Fewer requests to `bible-api.com`
   - Lower risk of rate limiting (429 errors)
   - Better API usage patterns

3. **Better User Experience**
   - Faster response times for cached values
   - More reliable service (less dependent on external API)
   - Smoother workflow when working with the same books/chapters

4. **Scalability**
   - Cache grows organically as users query different books
   - No manual maintenance required
   - Persistent across application restarts

## Testing

Comprehensive test suite added in `tests/test_api_cache.py`:

### Test Coverage

1. **Cache Usage Tests**
   - `test_uses_cached_value_when_available` - Verifies cached values are used instead of API calls
   - `test_caches_value_after_calculation` - Verifies values are cached after calculation

2. **Error Handling Tests**
   - `test_handles_cache_failure_gracefully` - Verifies graceful fallback to API when cache fails

3. **Database Operation Tests**
   - `test_get_cached_max_chapter_returns_none_when_not_cached`
   - `test_set_and_get_cached_max_chapter`
   - `test_get_cached_max_verse_returns_none_when_not_cached`
   - `test_set_and_get_cached_max_verse`

4. **Cache Isolation Tests**
   - `test_cache_is_translation_specific` - Different translations have separate caches
   - `test_cache_is_book_specific` - Different books have separate caches
   - `test_cache_is_chapter_specific_for_verses` - Different chapters have separate verse caches

All tests use temporary databases to ensure isolation and cleanup.

### Test Implementation Notes

- Tests mock `app.db.queries.QueryDB` (not `app.api.QueryDB`) since the import is lazy
- Rate limiting tests were updated to mock cache as returning `None` to test API call scenarios
- All mocks use temporary database paths to avoid conflicts with production database

## Migration Notes

- **Automatic Migration**: Tables are created automatically on first use via `CREATE TABLE IF NOT EXISTS`
- **No Data Loss**: Existing databases are upgraded seamlessly
- **Backward Compatible**: Functions work identically if cache is unavailable
- **Circular Import Prevention**: Lazy imports ensure no circular dependency issues during module loading

## Usage Examples

### Before (No Cache)

```python
# First call: Makes multiple API calls with delays
max_chapter = calculate_max_chapter("John", "web")  # ~5-10 seconds

# Second call: Makes same API calls again
max_chapter = calculate_max_chapter("John", "web")  # ~5-10 seconds again
```

### After (With Cache)

```python
# First call: Makes API calls, caches result
max_chapter = calculate_max_chapter("John", "web")  # ~5-10 seconds

# Second call: Returns instantly from cache
max_chapter = calculate_max_chapter("John", "web")  # <0.01 seconds
```

## Performance Impact

- **First request**: No change (API call + cache write overhead is negligible)
- **Cached requests**: ~99% faster (no API calls, no network delays)
- **Memory**: Minimal (SQLite handles storage efficiently)
- **Database size**: Small increase (~100 bytes per cached entry)

## Future Enhancements

Potential improvements for future PRs:

1. **Cache Invalidation**: Add mechanism to refresh stale cache entries
2. **Cache Statistics**: Track cache hit/miss rates
3. **Bulk Cache Population**: Pre-populate cache for common books
4. **Cache Expiration**: Optional TTL for cache entries
5. **Cache Warming**: Pre-calculate common combinations on startup

## Files Changed

- `app/db/queries.py`: Added cache tables and methods
- `app/api.py`: Modified `calculate_max_chapter()` and `calculate_max_verse()` to use cache with lazy imports
- `tests/test_api_cache.py`: New comprehensive test suite
- `tests/test_api_rate_limiting.py`: Updated to handle cache scenarios

## Related Issues

- Addresses performance concerns with repeated API calls
- Reduces risk of rate limiting errors (429)
- Improves user experience with faster response times

## Technical Implementation Details

### Circular Import Resolution

The implementation uses **lazy imports** to prevent circular dependency issues:

```python
# Inside calculate_max_chapter() and calculate_max_verse()
try:
    from app.db.queries import QueryDB  # Imported only when needed
    with QueryDB() as db:
        # ... cache operations ...
except Exception as e:
    # Fall back to API if cache fails
```

This breaks the circular import chain:

- `app.api` → `app.db.queries` → `app.ui` → `app.api` ❌ (circular)
- `app.api` (lazy import) → `app.db.queries` ✅ (no circular dependency at module load time)

### Test Mocking Strategy

Tests mock `app.db.queries.QueryDB` rather than `app.api.QueryDB` because:

- `QueryDB` is not a module-level attribute in `app.api`
- The import happens inside functions, so we mock at the source module
- This ensures tests accurately reflect the runtime behavior

## Review Checklist

- [x] Database schema changes are backward compatible
- [x] Error handling is robust (cache failures don't break functionality)
- [x] Tests cover all major scenarios
- [x] Code follows project style guidelines
- [x] Documentation is clear and comprehensive
- [x] No breaking changes to public APIs
- [x] Performance improvements are measurable
- [x] Circular import issues resolved with lazy imports
- [x] All tests pass in CI/CD pipeline
