# Translation Comparison Statistics

This document describes the statistical analysis functionality for translation comparisons in clible.

## Overview

The translation comparison feature now includes detailed statistical analysis that helps users understand the differences and similarities between two Bible translations quantitatively.

## Changes Made

### 1. Removed Old `compare_analyses` Function

**Location**: `app/analytics/analysis_tracker.py`

**Reason**: The old `compare_analyses` function was designed to compare word frequency analyses (same translation, different passages), not translation comparisons. It was:
- Not used in the UI
- Not suitable for comparing translations
- Confusing in its purpose

### 2. Created `calculate_translation_differences` Function

**Location**: `app/analytics/translation_compare.py`

**Purpose**: Calculates statistical differences between two translations of the same verses.

**Features**:
- Calculates overall text similarity ratio (0.0 to 1.0)
- Counts total words in each translation
- Identifies unique vocabulary in each translation
- Identifies common vocabulary between translations
- Calculates per-verse similarity ratios
- Limits displayed unique words to top 20 for readability

**Implementation Details**:
```python
def calculate_translation_differences(comparison_data: dict) -> dict
```

**Returns**:
```python
{
    "similarity_ratio": float,        # Overall similarity (0.0 to 1.0)
    "word_count_1": int,              # Total words in translation 1
    "word_count_2": int,              # Total words in translation 2
    "unique_words_1": list,           # Words only in translation 1 (limited to 20)
    "unique_words_2": list,           # Words only in translation 2 (limited to 20)
    "common_words_count": int,        # Number of common words
    "unique_count_1": int,            # Total unique words in translation 1
    "unique_count_2": int,            # Total unique words in translation 2
    "verse_similarities": list        # Per-verse similarity ratios
}
```

**Word Tokenization**:
- Uses regex pattern: `\b[a-z0-9']+\b` (case-insensitive)
- Includes alphanumeric words and contractions
- Normalizes to lowercase for comparison

**Similarity Algorithm**:
- Uses `difflib.SequenceMatcher` for text similarity
- Compares lowercase versions of texts
- Calculates both overall and per-verse similarities

### 3. Integrated Statistics into Display

**Location**: `app/analytics/translation_compare.py` → `render_side_by_side_comparison`

**Display Format**:
```
Translation Statistics:
  Overall Similarity: 85.5%
  Word Count (WEB): 245
  Word Count (KJV): 258
  Common Vocabulary: 180 words
  Unique to WEB: 25 words
  Unique to KJV: 33 words
  Sample unique words (WEB): beloved, everlasting, grace...
  Sample unique words (KJV): thee, thou, thy...
```

**Color Coding**:
- Yellow: Similarity percentage
- Green: Translation 1 statistics
- Blue: Translation 2 statistics
- Magenta: Common vocabulary
- Dim: Sample word lists

### 4. Updated Save Functionality

**Location**: `app/menus/analytics_menu.py`

**Changes**:
- Statistics are now calculated before saving
- Statistics are included in `scope_details` when saving to database
- This allows historical analysis of translation differences

**Database Storage**:
```json
{
  "translation1": "web",
  "translation2": "kjv",
  "statistics": {
    "similarity_ratio": 0.855,
    "word_count_1": 245,
    "word_count_2": 258,
    ...
  }
}
```

### 5. Testing

**New Test File**: `tests/test_translation_compare_stats.py`

**Test Coverage**:
- ✅ Basic statistics calculation
- ✅ Unique word identification
- ✅ Common word counting
- ✅ Multiple verse handling
- ✅ Empty data handling
- ✅ Case-insensitive comparison
- ✅ Identical text similarity
- ✅ Display limit for unique words

**Test Results**: All 93 tests pass

## Usage Example

### Command Line
```bash
# In Analytics Menu → Compare Translations
Book: John
Chapter: 3
Verses: 16 (or press Enter for entire chapter)
First Translation: web
Second Translation: kjv
```

### Output
```
┌─────────────────────────────────────────────────────────────┐
│                       John 3:16                              │
├─────────────────────────┬───────────────────────────────────┤
│ WEB                     │ KJV                                │
├─────────────────────────┼───────────────────────────────────┤
│ [16] For God so loved   │ [16] For God so loved the world,  │
│ the world, that he gave │ that he gave his only begotten    │
│ his one and only Son... │ Son...                            │
└─────────────────────────┴───────────────────────────────────┘

Translation Statistics:
  Overall Similarity: 87.3%
  Word Count (WEB): 28
  Word Count (KJV): 29
  Common Vocabulary: 22 words
  Unique to WEB: 3 words
  Unique to KJV: 4 words
  Sample unique words (WEB): one, only
  Sample unique words (KJV): begotten, thee

Save this comparison to history? (y/n): y
✓ Comparison saved to history!
```

## Implementation Notes

### Why Remove `compare_analyses`?

The old function was designed for a different use case:
- **Old**: Compare word frequencies across different passages in the same translation
- **New**: Compare the same passage across different translations

The statistical measures needed are fundamentally different:
- **Old**: Common words, frequency changes, unique vocabulary per passage
- **New**: Text similarity, vocabulary overlap, translation-specific terms

### Performance Considerations

**Word Tokenization**: Simple regex-based approach is fast for typical verse ranges
**Similarity Calculation**: `SequenceMatcher` is efficient for short texts (verses)
**Memory Usage**: Limited unique word display (20 words) prevents excessive memory use

### Future Enhancements

Potential improvements:
1. **Advanced Tokenization**: Use NLTK or spaCy for better word segmentation
2. **Semantic Analysis**: Identify similar words (synonyms) across translations
3. **Readability Metrics**: Calculate reading level differences
4. **Chart Visualization**: Plot similarity scores for verse ranges
5. **Comparison History**: Trend analysis of translation preferences

## References

- **Similarity Algorithm**: Python's `difflib.SequenceMatcher`
- **Regular Expressions**: Python's `re` module
- **Testing Framework**: pytest

## Related Documentation

- [`VALIDATION_REFACTORING.md`](VALIDATION_REFACTORING.md) - Input validation changes
- [`MAX_VERSE_CALCULATION.md`](MAX_VERSE_CALCULATION.md) - "All" keyword functionality
- [`PR_TRANSLATION_COMPARISON.md`](PR_TRANSLATION_COMPARISON.md) - Original translation comparison feature

---

**Last Updated**: 2026-01-21
**Author**: clible development team

