# AnalysisTracker - Pikaopas

## 🚀 Nopea Aloitus

```python
from app.analytics.analysis_tracker import AnalysisTracker
from app.state import AppState

# 1. Luo tracker
state = AppState()
tracker = AnalysisTracker(
    user_id=state.current_user_id,
    session_id=state.current_session_id
)

# 2. Tallenna analyysi
analysis_id = tracker.save_word_frequency_analysis(
    word_freq=[("jesus", 120), ("lord", 85)],
    vocab_info={"total_tokens": 1500, "vocabulary_size": 450},
    scope_type="query",
    scope_details={"query_id": "abc123"},
    verse_count=25
)

# 3. Hae historia
history = tracker.get_analysis_history(limit=10)

# 4. Hae yksittäinen
results = tracker.get_analysis_results(analysis_id)

# 5. Vertaile kahta
comparison = tracker.compare_analyses(id1, id2)
```

---

## 📋 Metodit Pähkinänkuoressa

### `save_word_frequency_analysis(word_freq, vocab_info, scope_type, scope_details, verse_count, chart_paths=None)`

**IN:** Lists/dicts  
**OUT:** `analysis_id` (string)  
**DO:** Tallentaa word freq + vocab stats → database

### `save_phrase_analysis(bigrams, trigrams, scope_type, scope_details, verse_count, chart_paths=None)`

**IN:** Lists of tuples  
**OUT:** `analysis_id` (string)  
**DO:** Tallentaa bigrams + trigrams → database

### `get_analysis_history(limit=10, analysis_type=None, scope_type=None)`

**IN:** Suodattimet (optional)  
**OUT:** `list[dict]` - Lista analyysejä  
**DO:** Hakee metadata, uusin ensin

### `get_analysis_results(analysis_id)`

**IN:** `analysis_id` (string)  
**OUT:** `dict` tai `None`  
**DO:** Hakee yksi analyysi KAIKKINEEN

### `compare_analyses(analysis_id1, analysis_id2)`

**IN:** Kaksi ID:tä  
**OUT:** `dict` tai `None`  
**DO:** Vertaa sanoja, löytää erot

---

## 🔑 Avaintermit

| Termi           | Selitys                      | Esimerkki                                                  |
| --------------- | ---------------------------- | ---------------------------------------------------------- |
| `analysis_id`   | Uniikki tunniste analyysille | `"a3b4c5d6"`                                               |
| `analysis_type` | Analyysin tyyppi             | `"word_frequency"` / `"phrase_analysis"`                   |
| `scope_type`    | Analyysin laajuus            | `"query"` / `"session"` / `"book"` / `"multi_query"`       |
| `scope_details` | JSON dict scopesta           | `{"query_id": "abc123"}`                                   |
| `result_type`   | Tuloksen tyyppi              | `"word_freq"` / `"vocab_stats"` / `"bigram"` / `"trigram"` |
| `result_data`   | JSON string tuloksista       | `'[["jesus", 120]]'`                                       |

---

## 🗄️ Tietokantataulut

```
analysis_history
├─ id (TEXT, PK)
├─ user_id (TEXT)
├─ session_id (TEXT, NULL OK)
├─ analysis_type (TEXT) - "word_frequency" / "phrase_analysis"
├─ scope_type (TEXT) - "query" / "session" / "book" / "multi_query"
├─ scope_details (TEXT, JSON)
├─ verse_count (INTEGER)
└─ created_at (TIMESTAMP)

analysis_results
├─ id (TEXT, PK)
├─ analysis_id (TEXT, FK → analysis_history.id)
├─ result_type (TEXT) - "word_freq" / "vocab_stats" / "bigram" / "trigram"
├─ result_data (TEXT, JSON)
├─ chart_path (TEXT, NULL OK)
└─ created_at (TIMESTAMP)
```

---

## 💡 Yleisimmät Käyttötapaukset

### 1. Tallenna analyysitulokset CLI:stä

```python
# cli.py:ssä
if input("\nSave this analysis to history? (y/n): ").lower() == 'y':
    from app.analytics.analysis_tracker import AnalysisTracker
    from app.state import AppState

    state = AppState()
    tracker = AnalysisTracker(
        user_id=state.current_user_id,
        session_id=state.current_session_id
    )

    analysis_id = tracker.save_word_frequency_analysis(
        word_freq=top_words,
        vocab_info=vocab_info,
        scope_type="query",
        scope_details={"query_id": selected_query['id']},
        verse_count=len(verse_data)
    )

    console.print(f"[green]✓ Saved: {analysis_id}[/green]")
```

### 2. Näytä analyysien historia

```python
history = tracker.get_analysis_history(limit=10)

for item in history:
    print(f"{item['id'][:8]} | {item['analysis_type']:15} | "
          f"{item['scope_type']:10} | {item['verse_count']} verses | "
          f"{item['created_at']}")
```

### 3. Vertaile Johanneksen ja Matteuksen analyysiä

```python
# User valitsee kaksi analyysiä
comparison = tracker.compare_analyses(john_id, matthew_id)

print(f"\n=== YHTEISET SANAT ({len(comparison['common_words'])}) ===")
for word, c1, c2 in comparison['common_words'][:10]:
    print(f"{word:15} | {c1:4} → {c2:4}")

print(f"\n=== VAIN JOHANNEKSESSA ({len(comparison['unique_to_first'])}) ===")
for word, count in comparison['unique_to_first'][:5]:
    print(f"{word:15} | {count}")
```

---

## ⚠️ Yleisimmät Virheet

### 1. Unohdit asettaa user_id

```python
# VÄÄRIN
tracker = AnalysisTracker()  # user_id = None

# OIKEIN
state = AppState()
tracker = AnalysisTracker(user_id=state.current_user_id)
```

### 2. JSON ei serialisoidu

```python
# VÄÄRIN
result_data = word_freq  # list[tuple]

# OIKEIN
result_data = json.dumps(word_freq)  # string
```

### 3. Väärä analysis_type filtterissä

```python
# VÄÄRIN
history = tracker.get_analysis_history(analysis_type="word_freq")

# OIKEIN
history = tracker.get_analysis_history(analysis_type="word_frequency")
```

---

## 🧪 Testaus

```bash
# Kaikki testit
pytest tests/test_analysis_tracker.py -v

# Vain yksi luokka
pytest tests/test_analysis_tracker.py::TestSaveWordFrequencyAnalysis -v

# Vain yksi testi
pytest tests/test_analysis_tracker.py::TestSaveWordFrequencyAnalysis::test_save_creates_analysis_id -v
```

---

## 📊 Suorituskykytietoa

- **Tallennus:** ~10-20ms per analyysi
- **Haku (history):** ~5ms per 10 riviä
- **Haku (results):** ~10-15ms per analyysi (JOIN)
- **Vertailu:** ~20-30ms (2x haku + set-operaatiot)

---

## 🔗 Linkit

- [Täydellinen dokumentaatio](./ANALYSIS_TRACKER_LOGIC.md)
- [Testit](../tests/test_analysis_tracker.py)
- [Lähdekoodi](../app/analytics/analysis_tracker.py)
- [Tietokantaskeema](../app/db/queries.py#L529-L563)

---

**Viimeksi päivitetty:** 2026-01-15
