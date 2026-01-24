# Analysis Tracking Integration - Complete Documentation

## 📋 Overview

This document describes the integration of analysis tracking functionality into the CLI application. Users can now save their analysis results (word frequency, phrase analysis) to a database history for later retrieval, comparison, and review.

---

## 🎯 What Was Implemented

### 1. Core Features

- **Save to History** - Save analysis results with metadata
- **View History** - Browse all saved analyses
- **Filter History** - Filter by analysis type or scope
- **View Details** - Inspect specific analysis with full results
- **Automatic Metadata** - User ID, session ID, timestamps tracked automatically

### 2. Integration Points

Analysis tracking was integrated into **5 analytics menu options**:

| Menu Option | Analysis Type | Scope Type | Description |
|-------------|--------------|------------|-------------|
| Choice 2 | Word Frequency | `query` | Single saved query analysis |
| Choice 3 | Phrase Analysis | `query` | Single saved query bigrams/trigrams |
| Choice 4 | Both | `session` | Current session analysis |
| Choice 5 | Both | `multi_query` | Multiple queries combined |
| Choice 6 | Both | `book` | Entire book analysis |
| Choice 7 | - | - | **History Menu** (NEW) |

---

## 🏗️ Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────┐
│                   CLI (app/cli.py)                   │
│  - User interaction                                  │
│  - Prompts for "Save to history?"                    │
│  - History menu (Choice 7)                           │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│         AnalysisTracker (analysis_tracker.py)       │
│  - save_word_frequency_analysis()                    │
│  - save_phrase_analysis()                            │
│  - get_analysis_history()                            │
│  - get_analysis_results()                            │
│  - compare_analyses()                                │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│              Database (SQLite)                       │
│  Tables:                                             │
│  - analysis_history (metadata)                       │
│  - analysis_results (actual data)                    │
└─────────────────────────────────────────────────────┘
```

### Data Flow

```
1. User performs analysis
   └─> WordFrequencyAnalyzer/PhraseAnalyzer

2. Results displayed to user

3. User prompted: "Save to history?"
   └─> If YES:
       ├─> Get AppState (user_id, session_id)
       ├─> Create AnalysisTracker instance
       ├─> Call save_*_analysis()
       └─> Save to database (history + results)

4. Later: User accesses History Menu
   └─> View/filter/inspect saved analyses
```

---

## 📝 Implementation Details

### Choice 2: Word Frequency (Query)

**Location:** `app/cli.py` lines 278-294

**Flow:**
1. User selects saved query
2. Analysis performed and displayed
3. Visualization prompt
4. **Save prompt** → If yes:
   - Get `top_words` and `vocab_info`
   - Create tracker with user/session context
   - Save with `scope_type="query"`
   - Store `{"query_id": selected_query['id']}`

**Code Pattern:**
```python
if input("\nSave this analysis to history? (y/n): ").lower() == 'y':
    from app.analytics.analysis_tracker import AnalysisTracker
    from app.state import AppState
    
    state = AppState()
    tracker = AnalysisTracker(
        user_id=state.current_user_id,
        session_id=state.current_session_id
    )
    
    tracker.save_word_frequency_analysis(
        word_freq=top_words,
        vocab_info=vocab_info,
        scope_type="query",
        scope_details={"query_id": selected_query['id']},
        verse_count=len(verse_data)
    )
    console.print("[green]✓ Analysis saved to history![/green]")
```

---

### Choice 3: Phrase Analysis (Query)

**Location:** `app/cli.py` lines 328-352

**Changes from original:**
- **Fixed:** Moved save block from `else` block (where `verse_data` didn't exist) to `if verse_data:` block
- **Fixed:** Removed debug prints
- **Fixed:** Removed unnecessary user_id/session_id validation
- **Fixed:** Simplified success message

**Key Differences:**
- Uses `save_phrase_analysis()` instead of `save_word_frequency_analysis()`
- Saves `bigrams` and `trigrams` data
- Result types: `"bigram"` and `"trigram"`

---

### Choice 4: Session Analysis

**Location:** `app/cli.py` lines 411-445

**Special Handling:**
- Can save **both** word frequency AND phrase analysis
- Uses `scope_type="session"`
- Stores `{"session_id": state.current_session_id}`
- Conditionally saves based on `analysis_choice`:
  - `'1'` or `'3'` → Save word frequency
  - `'2'` or `'3'` → Save phrase analysis

**Scope Details:**
```python
scope_details={"session_id": state.current_session_id}
```

This allows tracking which session the analysis was performed in.

---

### Choice 5: Multiple Queries Analysis

**Location:** `app/cli.py` lines 537-571

**Critical Fix:**
- **Original:** `scope_type="query"` ❌
- **Fixed:** `scope_type="multi_query"` ✅

**Scope Details:**
```python
scope_details={"query_ids": selected_ids}  # List of query IDs
```

**Why Important:**
- Distinguishes single query from multi-query analyses
- Allows proper filtering in history menu
- Enables comparison features in future

---

### Choice 6: Book Analysis

**Location:** `app/cli.py` lines 661-695

**Critical Fix:**
- **Original:** `{"book_name": selected_book}` ❌
- **Fixed:** `{"book": selected_book}` ✅

**Why Important:**
- Consistency with test expectations
- Matches scope_details pattern: `{"book": "John"}`

**Example:**
```python
tracker.save_word_frequency_analysis(
    ...
    scope_type="book",
    scope_details={"book": "Revelation"},  # Correct field name
    ...
)
```

---

### Choice 7: History Menu (NEW)

**Location:** `app/cli.py` lines 697-873

**Features:**

#### Submenu 1: View All Analyses
- Lists all analyses (limit 20)
- Shows: Type, Scope, Verse count, Created timestamp
- Formatted table output

**Output Example:**
```
Analysis History (15 records):

#    Type                  Scope          Verses   Created
──────────────────────────────────────────────────────────────────────
1    word_frequency       query          25       2025-01-15 10:30:15
2    phrase_analysis      session        150      2025-01-15 09:45:22
3    word_frequency       book           1273     2025-01-14 14:20:05
...
```

#### Submenu 2: Filter by Type
- Filter by `word_frequency` or `phrase_analysis`
- Reduces noise for specific analysis types

#### Submenu 3: View Specific Analysis
- Select by number or ID
- Full analysis details displayed:
  - Metadata (ID, type, scope, verses, created date)
  - Scope details (JSON formatted)
  - Results preview (top 5 items)
  - Visualization paths (if available)

**Output Example:**
```
═══ Analysis Details ═══
ID:           a3b4c5d6
Type:         word_frequency
Scope:        query
Verses:       25
Created:      2025-01-15 10:30:15

Scope Details: {
  "query_id": "abc123"
}

Results:
word_freq:
  jesus                          120
  lord                            85
  god                             65
  love                            45
  faith                           30

vocab_stats:
  total_tokens: 1500
  vocabulary_size: 450
  type_token_ratio: 0.3

Visualizations:
  word_freq: data/charts/word_frequency/2025-01-15_10-30-15_word_freq.png
```

---

## 🔑 Key Concepts

### Scope Types

| Scope Type | Use Case | Details Example |
|------------|----------|-----------------|
| `query` | Single saved query | `{"query_id": "abc123"}` |
| `session` | Current session | `{"session_id": "def456"}` |
| `book` | Entire book | `{"book": "John"}` |
| `multi_query` | Multiple queries | `{"query_ids": ["abc", "def"]}` |

### Analysis Types

| Analysis Type | Result Types | Data Stored |
|---------------|--------------|-------------|
| `word_frequency` | `word_freq`, `vocab_stats` | Word counts + vocabulary statistics |
| `phrase_analysis` | `bigram`, `trigram` | 2-word and 3-word phrase counts |

### User Context

Every analysis is tagged with:
- **`user_id`** - Who performed the analysis (from `AppState`)
- **`session_id`** - In which session (optional, from `AppState`)
- **`created_at`** - When it was saved (automatic timestamp)

This allows:
- User-specific history (privacy)
- Session-based filtering
- Temporal tracking

---

## 🛡️ Error Handling

### User Not Authenticated

```python
if not state.current_user_id:
    console.print("[yellow]Please log in to view analysis history.[/yellow]")
    input("Press any key to continue...")
    continue
```

### No History Found

```python
history = tracker.get_analysis_history(limit=20)

if not history:
    console.print("[yellow]No analysis history found.[/yellow]")
```

### Analysis Not Found

```python
results = tracker.get_analysis_results(analysis_id)

if not results:
    console.print(f"[red]Analysis {analysis_id} not found.[/red]")
```

---

## 📊 Database Schema

### Table: `analysis_history`

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT | UUID (8 chars) |
| `user_id` | TEXT | Foreign key to users |
| `session_id` | TEXT | Foreign key to sessions (nullable) |
| `analysis_type` | TEXT | "word_frequency" / "phrase_analysis" |
| `scope_type` | TEXT | "query" / "session" / "book" / "multi_query" |
| `scope_details` | TEXT | JSON string |
| `verse_count` | INTEGER | Number of verses analyzed |
| `created_at` | TIMESTAMP | Auto-generated |

### Table: `analysis_results`

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT | UUID (8 chars) |
| `analysis_id` | TEXT | Foreign key to analysis_history |
| `result_type` | TEXT | "word_freq" / "vocab_stats" / "bigram" / "trigram" |
| `result_data` | TEXT | JSON string of actual results |
| `chart_path` | TEXT | Path to visualization (nullable) |
| `created_at` | TIMESTAMP | Auto-generated |

### Indexes

```sql
CREATE INDEX idx_analysis_user ON analysis_history(user_id);
CREATE INDEX idx_analysis_type ON analysis_history(analysis_type);
CREATE INDEX idx_analysis_session ON analysis_history(session_id);
CREATE INDEX idx_analysis_date ON analysis_history(created_at);
CREATE INDEX idx_results_analysis ON analysis_results(analysis_id);
```

---

## 🧪 Testing

All functionality is covered by 31 unit tests in `tests/test_analysis_tracker.py`:

- ✅ Save word frequency analysis (8 tests)
- ✅ Save phrase analysis (5 tests)
- ✅ Get analysis history (5 tests)
- ✅ Get analysis results (4 tests)
- ✅ Compare analyses (5 tests)
- ✅ Edge cases (4 tests)

**Run tests:**
```bash
pytest tests/test_analysis_tracker.py -v
```

---

## 🔧 Common Issues & Fixes

### Issue 1: "verse_data not defined"

**Symptom:** Error when trying to save analysis

**Cause:** Save block in wrong location (outside `if verse_data:` block)

**Fix:** Ensure save prompt is **inside** the `if verse_data:` block

---

### Issue 2: Wrong scope_type

**Symptom:** Can't filter analyses correctly in history menu

**Cause:** Using `"query"` instead of `"multi_query"` for multiple queries

**Fix:**
```python
# Wrong
scope_type="query"

# Correct
scope_type="multi_query"
```

---

### Issue 3: Wrong scope_details field

**Symptom:** Book name not displaying correctly in history

**Cause:** Using `{"book_name": ...}` instead of `{"book": ...}`

**Fix:**
```python
# Wrong
scope_details={"book_name": selected_book}

# Correct
scope_details={"book": selected_book}
```

---

## 📚 Related Documentation

- [AnalysisTracker Logic](./ANALYSIS_TRACKER_LOGIC.md) - Deep dive into tracker implementation
- [Quick Reference](./ANALYSIS_TRACKER_QUICK_REFERENCE.md) - Quick lookup for methods
- [Tests](../tests/test_analysis_tracker.py) - Complete test suite

---

## 🚀 Future Enhancements

### Planned Features

1. **Compare Analyses** - Side-by-side comparison of two analyses
   - Common words
   - Unique words
   - Frequency changes
   - Visual diff charts

2. **Export Reports** - Generate PDF/Markdown reports
   - Include visualizations
   - Formatted tables
   - Summary statistics

3. **Bulk Operations**
   - Delete multiple analyses
   - Export multiple analyses
   - Tag/categorize analyses

4. **Advanced Filtering**
   - Date range filters
   - Verse count ranges
   - Combined filters (type + scope + date)

5. **Analysis Annotations**
   - Add notes to saved analyses
   - Mark favorites
   - Share with other users

---

## ✅ Checklist for Merge

- [x] All 5 analysis options have "Save to history?" prompts
- [x] History menu (Choice 7) implemented
- [x] All scope_types correct
- [x] All scope_details fields correct
- [x] No debug prints left
- [x] No duplicate success messages
- [x] Proper error handling
- [x] User authentication checks
- [x] JSON import added
- [x] .gitignore updated (data/charts/)
- [x] All tests pass (31/31)
- [x] Documentation complete

---

**Last Updated:** 2026-01-16  
**Author:** AI Assistant + vvirtai  
**Branch:** feature/add-visualization  
**Status:** Ready for merge ✅
