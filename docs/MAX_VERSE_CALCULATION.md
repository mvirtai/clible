# Max Verse and Chapter Calculation Feature

## Overview

This document describes the functionality that automatically calculates:
1. The maximum verse number in a chapter when users specify empty string or 'all' for verses input
2. The maximum chapter number in a book when users specify 'all' for chapter input

This allows fetching all verses in a chapter or the last chapter in a book without manually specifying the numbers.

## Feature Description

### For Verses

When a user provides an empty string (`""`) or the keyword `"all"` for verses input, the system:

1. Fetches the entire chapter from the API
2. Analyzes the response to find the maximum verse number
3. Constructs a verse range `"1-{max_verse}"` 
4. Uses this range to fetch all verses in the chapter

### For Chapters

When a user provides the keyword `"all"` for chapter input, the system:

1. Attempts to find the maximum chapter number for the book
2. Uses an optimized search strategy (tries common chapter numbers first)
3. Replaces `"all"` with the calculated max chapter number
4. Uses this chapter number for the API request

## Implementation Details

### New Function: `calculate_max_chapter()`

**Location:** `app/api.py`

**Purpose:** Calculate the maximum chapter number in a book by attempting to fetch chapters and finding the highest valid chapter number.

**Signature:**
```python
def calculate_max_chapter(book: str, translation: str | None = None) -> int | None
```

**How it works:**
1. First verifies the book exists by fetching chapter 1
2. Tries common high chapter numbers (50, 30, 20, 10) to quickly narrow down the range
3. Searches upward from the highest found chapter to find the actual maximum
4. Returns the maximum chapter number, or `None` if unable to determine

**Example:**
```python
max_chapter = calculate_max_chapter("Romans", "web")
# Returns: 16 (if Romans has 16 chapters)
```

### New Function: `calculate_max_verse()`

**Location:** `app/api.py`

**Purpose:** Calculate the maximum verse number in a chapter by fetching the chapter and analyzing the response.

**Signature:**

```python
def calculate_max_verse(book: str, chapter: str, translation: str | None = None) -> int | None
```

**How it works:**

1. Fetches the entire chapter from the API (without verse specification)
2. Extracts the `verses` array from the response
3. Finds the maximum `verse` number from all verses in the array
4. Returns the maximum verse number, or `None` if unable to determine

**Example:**

```python
max_verse = calculate_max_verse("John", "3", "web")
# Returns: 36 (if John 3 has 36 verses)
```

### Updated Function: `fetch_by_reference()`

**Location:** `app/api.py`

**Changes:**

- Added logic to detect empty string or 'all' for verses parameter
- Calls `calculate_max_verse()` when empty/'all' is detected
- Constructs verse range `"1-{max_verse}"` if max verse is successfully calculated
- Falls back to fetching entire chapter if max verse calculation fails

**Logic Flow:**

```python
if verses is not None and verses.strip().lower() in ("", "all"):
    max_verse = calculate_max_verse(book, chapter, translation)
    if max_verse:
        verses = f"1-{max_verse}"  # Use calculated range
    else:
        verses = None  # Fallback to entire chapter
```

### Updated Validation: `validate_verses()`

**Location:** `app/validations/validations.py`

**Changes:**

- Now accepts `"all"` as a valid input (case-insensitive)
- Returns `"all"` as the validated payload when `allow_empty=True`
- Empty string and `"all"` are both treated as requests for entire chapter

**Example:**

```python
is_valid, payload = validate_verses("all", allow_empty=True)
# Returns: (True, "all")
```

## Usage Examples

### In Analytics Menu

```python
# User can press Enter or type 'all'
verses_input = click.prompt(
    "Verses (press Enter or type 'all' for entire chapter)",
    type=VersesParam(),
    default="",
    show_default=False
)

# Empty string or 'all' triggers max verse calculation
comparison_data = fetch_verse_comparison(book, chapter, verses_input, trans1, trans2)
```

### Direct API Usage

```python
# Empty string triggers max verse calculation
data = fetch_by_reference("John", "3", "")

# 'all' for verses triggers max verse calculation  
data = fetch_by_reference("John", "3", "all")

# 'all' for chapter triggers max chapter calculation
data = fetch_by_reference("Romans", "all", None)

# Both chapter and verses can be 'all'
data = fetch_by_reference("Romans", "all", "all")
# This will: calculate max chapter, then calculate max verse for that chapter
```

## Benefits

1. **User Convenience:** Users don't need to know the exact number of verses in a chapter
2. **Automatic Detection:** System automatically determines chapter length
3. **Consistent Behavior:** Empty string and 'all' both work the same way
4. **Fallback Safety:** If calculation fails, falls back to fetching entire chapter

## Error Handling

- If `calculate_max_verse()` fails (network error, API error, etc.), the system falls back to fetching the entire chapter
- If the chapter response has no verses, `calculate_max_verse()` returns `None` and fallback is used
- All errors are logged for debugging purposes

## Performance Considerations

- **Additional API Call:** Calculating max verse requires an extra API call to fetch the chapter
- **Caching Opportunity:** Future enhancement could cache max verse numbers per book/chapter
- **Efficiency:** The extra call is only made when empty/'all' is specified

## Testing

To test this functionality:

1. **Test with empty string:**

   ```python
   data = fetch_by_reference("John", "3", "")
   # Should fetch all verses in John 3
   ```

2. **Test with 'all':**

   ```python
   data = fetch_by_reference("John", "3", "all")
   # Should fetch all verses in John 3
   ```

3. **Test validation:**
   ```python
   is_valid, payload = validate_verses("all", allow_empty=True)
   assert is_valid == True
   assert payload == "all"
   ```

## Related Files

- `app/api.py` - Contains `calculate_max_verse()` and updated `fetch_by_reference()`
- `app/validations/validations.py` - Contains updated `validate_verses()` function
- `app/menus/analytics_menu.py` - Uses the new functionality in translation comparison
- `app/validations/click_params.py` - `VersesParam` handles 'all' input

## Future Enhancements

1. **Caching:** Cache max verse numbers to avoid repeated API calls
2. **Database Storage:** Store max verse numbers in database for faster lookups
3. **Batch Calculation:** Pre-calculate max verses for all chapters during initialization
4. **User Feedback:** Show calculated max verse to user before fetching
