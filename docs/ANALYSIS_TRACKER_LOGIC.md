# AnalysisTracker - Logiikka ja Toteutus

## 📚 Sisällysluettelo

1. [Yleiskatsaus](#yleiskatsaus)
2. [Arkkitehtuuri](#arkkitehtuuri)
3. [Metodien Logiikka](#metodien-logiikka)
4. [Tietokantaskeema](#tietokantaskeema)
5. [Käyttöesimerkit](#käyttöesimerkit)
6. [Debuggaus ja Troubleshooting](#debuggaus-ja-troubleshooting)

---

## Yleiskatsaus

`AnalysisTracker` on luokka, joka tallentaa analyysitulokset tietokantaan tulevaa käyttöä varten. Sen avulla voidaan:

- 💾 **Tallentaa** analyysitulokset (sanafrekvenssit, fraasit)
- 📊 **Hakea** analyysien historiaa suodattimilla
- 🔍 **Tarkastella** yksittäisiä analyysejä yksityiskohtaisesti
- ⚖️ **Vertailla** kahta analyysiä keskenään

### Keskeiset Käsitteet

**Analysis History** = Metadata (milloin, kuka, mitä, kuinka paljon)  
**Analysis Results** = Varsinaiset tulokset (JSON-muodossa)  
**Scope** = Analyysin laajuus (yksittäinen query, session, kirja, jne.)

---

## Arkkitehtuuri

### Luokan Rakenne

```python
class AnalysisTracker:
    def __init__(self, user_id, session_id, db_path):
        self.user_id = user_id         # Kuka analyysejä tekee
        self.session_id = session_id   # Missä sessiossa (valinnainen)
        self.db_path = db_path         # Mihin tietokantaan (testaus)
```

### Dependency Injection Pattern

```python
def _get_db(self):
    """Palauttaa QueryDB-instanssin oikealla polulla"""
    if self.db_path is None:
        return QueryDB()              # Tuotanto: default database
    return QueryDB(self.db_path)      # Testit: temporary database
```

**Miksi tämä on tärkeää?**

- Testit käyttävät väliaikaista tietokantaa (`/tmp/...`)
- Tuotanto käyttää oikeaa tietokantaa (`data/clible.db`)
- Sama koodi toimii molemmissa ympäristöissä

---

## Metodien Logiikka

### 1. `save_word_frequency_analysis()`

**Tarkoitus:** Tallentaa sanafrekvenssien analyysin

**Vaiheet:**

```python
# VAIHE 1: Luo uniikki ID
analysis_id = uuid.uuid4().hex[:8]  # Esim: "a3b4c5d6"

# VAIHE 2: Tallenna metadata
INSERT INTO analysis_history (
    id, user_id, session_id,
    analysis_type,      # "word_frequency"
    scope_type,         # "query", "session", "book", "multi_query"
    scope_details,      # JSON: {"query_id": "abc123"}
    verse_count         # 25
)

# VAIHE 3: Tallenna word_freq tulokset
INSERT INTO analysis_results (
    id,                 # Uusi UUID
    analysis_id,        # Linkki historiaan
    result_type,        # "word_freq"
    result_data,        # JSON: [["jesus", 120], ["lord", 85], ...]
    chart_path          # "data/charts/..."
)

# VAIHE 4: Tallenna vocab_stats tulokset
INSERT INTO analysis_results (
    ...
    result_type,        # "vocab_stats"
    result_data,        # JSON: {"total_tokens": 1500, ...}
    ...
)

# VAIHE 5: Commit ja palauta ID
db.conn.commit()
return analysis_id
```

**Kriittiset kohdat:**

1. **JSON Serialisointi**

   ```python
   json.dumps(word_freq)         # list[tuple] → string
   json.dumps(scope_details)     # dict → string
   ```

   - **Miksi?** SQLite ei tue listoja/dictionaryja suoraan
   - Tuples muuttuvat automaattisesti listoiksi JSONissa

2. **Chart Paths** (valinnainen)
   ```python
   chart_paths.get('word_freq') if chart_paths else None
   ```
   - Jos visualisointeja ei tehty → `None`
   - Jos tehty → polku tiedostoon

---

### 2. `save_phrase_analysis()`

**Tarkoitus:** Tallentaa bigrammi- ja trigrammi-analyysin

**Ero word_frequency:hin:**

- `analysis_type = "phrase_analysis"` (ei "word_frequency")
- **Kaksi** result-tietuetta:
  - `result_type = "bigram"` → bigram data
  - `result_type = "trigram"` → trigram data

**Logiikka on muuten identtinen** → koodi on melkein kopio `save_word_frequency_analysis()`:sta

---

### 3. `get_analysis_history()`

**Tarkoitus:** Hae analyysien metadata suodattimilla

**Dynaaminen SQL-kysely:**

```python
# Alkupiste - aina TRUE
query = "SELECT * FROM analysis_history WHERE 1=1"
params = []

# Lisää suodattimia dynaamisesti
if self.user_id:
    query += " AND user_id = ?"
    params.append(self.user_id)

if analysis_type:  # Esim: "word_frequency"
    query += " AND analysis_type = ?"
    params.append(analysis_type)

if scope_type:     # Esim: "book"
    query += " AND scope_type = ?"
    params.append(scope_type)

# Järjestys ja rajoitus
query += " ORDER BY created_at DESC, ROWID DESC LIMIT ?"
params.append(limit)
```

**Miksi dynaaminen?**

- Käyttäjä voi suodattaa **tai olla suodattamatta**
- Ei tarvitse kirjoittaa 8 eri SQL-kyselyä
- Parametrit estävät SQL-injektion

**Järjestys:**

- `ORDER BY created_at DESC` → Uusin ensin
- `, ROWID DESC` → Jos sama aikaleima, viimeisin rivi ensin

**ROWID Tiebreaker:**

```
Ongelma: 3 analyysiä luotu 0.001s sisällä → sama timestamp
Ratkaisu: ROWID (rivijärjestysnumero) kasvaa aina
         → Uusin rivi = suurin ROWID
```

---

### 4. `get_analysis_results()`

**Tarkoitus:** Hae yksi analyysi KAIKKINEEN (metadata + tulokset)

**SQL JOIN:**

```sql
SELECT
    h.*,                    -- Kaikki history-kentät
    r.result_type,          -- "word_freq", "vocab_stats"
    r.result_data,          -- JSON data
    r.chart_path            -- Polku kuvaan
FROM analysis_history h
LEFT JOIN analysis_results r ON h.id = r.analysis_id
WHERE h.id = ?
```

**LEFT JOIN?** Koska analyysillä voi olla 0-N tulosta (vaikka normaalisti 2)

**Tulos:** Yksi rivi per result_type:

```
| id   | user_id | analysis_type | result_type | result_data        |
|------|---------|---------------|-------------|--------------------|
| abc  | user1   | word_freq     | word_freq   | [["jesus", 120]]   |
| abc  | user1   | word_freq     | vocab_stats | {"total": 1500}    |
```

**Python-puolen logiikka:**

```python
rows = db.cur.fetchall()  # 2 riviä

# 1. Ota ensimmäinen rivi → metadata
first_row = rows[0]
analysis = {
    "id": first_row["id"],
    "user_id": first_row["user_id"],
    ...
    "results": {},        # Täytetään loopeissa
    "chart_paths": {}     # Täytetään loopeissa
}

# 2. Käy läpi KAIKKI rivit → deserialize JSON
for row in rows:
    result_type = row["result_type"]  # "word_freq" tai "vocab_stats"

    # Muuta JSON string → Python object
    data = json.loads(row["result_data"])

    # Lisää dictionaryyn
    analysis["results"][result_type] = data

    if row["chart_path"]:
        analysis["chart_paths"][result_type] = row["chart_path"]

return analysis
```

**JSON Deserialisointi:**

```python
# Tietokannassa (string):
'[["jesus", 120], ["lord", 85]]'

# Python-objektina (list):
[["jesus", 120], ["lord", 85]]
```

---

### 5. `compare_analyses()`

**Tarkoitus:** Vertaa kahta sanafrekvenssien analyysiä

**Vaiheet:**

```python
# 1. Hae molemmat analyysit
a1 = self.get_analysis_results(id1)
a2 = self.get_analysis_results(id2)

# 2. Tarkista että löytyivät
if not a1 or not a2:
    return None

# 3. Muuta listat → dictionaries
words_1 = dict(a1["results"]["word_freq"])
# {"jesus": 120, "lord": 85, "god": 65}

words_2 = dict(a2["results"]["word_freq"])
# {"jesus": 150, "love": 60, "peace": 40}
```

**Set-operaatiot:**

```python
# Yhteiset sanat (intersection)
common = set(words_1.keys()) & set(words_2.keys())
# {"jesus"}

# Uniikit analyysi 1:ssä (difference)
unique_1 = set(words_1.keys()) - set(words_2.keys())
# {"lord", "god"}

# Uniikit analyysi 2:ssa
unique_2 = set(words_2.keys()) - set(words_1.keys())
# {"love", "peace"}
```

**Frekvenssierot:**

```python
frequency_changes = []
for word in common:
    count1 = words_1[word]  # 120
    count2 = words_2[word]  # 150
    diff = count2 - count1  # +30

    frequency_changes.append((word, count1, count2, diff))

# Järjestä suurimmat muutokset ensin
frequency_changes.sort(key=lambda x: abs(x[3]), reverse=True)
```

**Palautusarvo:**

```python
{
    "analysis_1": {metadata...},
    "analysis_2": {metadata...},
    "common_words": [("jesus", 120, 150), ...],
    "unique_to_first": [("lord", 85), ("god", 65)],
    "unique_to_second": [("love", 60), ("peace", 40)],
    "frequency_changes": [("jesus", 120, 150, +30), ...]
}
```

---

## Tietokantaskeema

### Taulu: `analysis_history`

| Kenttä          | Tyyppi    | Kuvaus                                       |
| --------------- | --------- | -------------------------------------------- |
| `id`            | TEXT      | Uniikki tunniste (UUID)                      |
| `user_id`       | TEXT      | Kuka teki analyysin                          |
| `session_id`    | TEXT      | Session yhteydessä (NULL jos ei)             |
| `analysis_type` | TEXT      | "word_frequency" / "phrase_analysis"         |
| `scope_type`    | TEXT      | "query" / "session" / "book" / "multi_query" |
| `scope_details` | TEXT      | JSON: esim `{"query_id": "abc"}`             |
| `verse_count`   | INTEGER   | Analysoitujen jakeiden määrä                 |
| `created_at`    | TIMESTAMP | Automaattinen aikaleima                      |

### Taulu: `analysis_results`

| Kenttä        | Tyyppi    | Kuvaus                                             |
| ------------- | --------- | -------------------------------------------------- |
| `id`          | TEXT      | Uniikki tunniste                                   |
| `analysis_id` | TEXT      | Viittaus `analysis_history.id`                     |
| `result_type` | TEXT      | "word_freq" / "vocab_stats" / "bigram" / "trigram" |
| `result_data` | TEXT      | JSON: varsinaiset tulokset                         |
| `chart_path`  | TEXT      | Polku visualisointitiedostoon (NULL jos ei)        |
| `created_at`  | TIMESTAMP | Automaattinen aikaleima                            |

### Relaatio

```
analysis_history (1) ----< (N) analysis_results
       (yksi)                    (monta)

Yksi analyysi voi sisältää monta tulosta:
- Word frequency → word_freq + vocab_stats (2 kpl)
- Phrase analysis → bigram + trigram (2 kpl)
```

---

## Käyttöesimerkit

### Esimerkki 1: Tallenna Word Frequency

```python
from app.analytics.analysis_tracker import AnalysisTracker
from app.state import AppState

# Oletetaan käyttäjä kirjautunut
state = AppState()
tracker = AnalysisTracker(
    user_id=state.current_user_id,
    session_id=state.current_session_id
)

# Tallenna analyysi
analysis_id = tracker.save_word_frequency_analysis(
    word_freq=[("jesus", 120), ("lord", 85)],
    vocab_info={"total_tokens": 1500, "vocabulary_size": 450},
    scope_type="query",
    scope_details={"query_id": "abc123"},
    verse_count=25
)

print(f"Saved: {analysis_id}")  # "a3b4c5d6"
```

### Esimerkki 2: Hae Historia

```python
# Hae kaikki omat word frequency analyysit
history = tracker.get_analysis_history(
    limit=10,
    analysis_type="word_frequency"
)

for item in history:
    print(f"{item['created_at']}: {item['scope_type']} ({item['verse_count']} verses)")
```

### Esimerkki 3: Hae Yksittäinen Analyysi

```python
results = tracker.get_analysis_results("a3b4c5d6")

print(f"Type: {results['analysis_type']}")
print(f"Verses: {results['verse_count']}")

# Tulokset
word_freq = results["results"]["word_freq"]
print(f"Top word: {word_freq[0][0]} ({word_freq[0][1]} times)")

vocab = results["results"]["vocab_stats"]
print(f"Total tokens: {vocab['total_tokens']}")
```

### Esimerkki 4: Vertaile Analyysejä

```python
comparison = tracker.compare_analyses("abc123", "def456")

print("\n=== YHTEISET SANAT ===")
for word, count1, count2 in comparison["common_words"]:
    print(f"{word}: {count1} → {count2}")

print("\n=== VAIN ENSIMMÄISESSÄ ===")
for word, count in comparison["unique_to_first"]:
    print(f"{word}: {count}")

print("\n=== SUURIMMAT MUUTOKSET ===")
for word, c1, c2, diff in comparison["frequency_changes"][:5]:
    change = "+" if diff > 0 else ""
    print(f"{word}: {c1} → {c2} ({change}{diff})")
```

---

## Debuggaus ja Troubleshooting

### Ongelma 1: "Analysis not found"

```python
results = tracker.get_analysis_results("wrong_id")
# Returns: None
```

**Ratkaisu:** Tarkista että ID on oikein

```python
history = tracker.get_analysis_history()
print([h["id"] for h in history])  # Lista kaikista ID:istä
```

### Ongelma 2: JSON Decode Error

```python
# Virhe: json.decoder.JSONDecodeError
```

**Syy:** Tietokannassa väärin muotoiltu JSON

**Ratkaisu:** Tarkista `result_data`:

```sql
SELECT result_data FROM analysis_results WHERE analysis_id = 'abc123';
```

### Ongelma 3: Tyhjä historia

```python
history = tracker.get_analysis_history()
# Returns: []
```

**Tarkista:**

1. Onko `user_id` asetettu?
2. Onko tietokannassa dataa?
   ```sql
   SELECT COUNT(*) FROM analysis_history;
   ```

### Ongelma 4: Väärä järjestys

Jos analyysit eivät ole oikeassa järjestyksessä:

**Syy:** Kaikilla sama `created_at` timestamp

**Ratkaisu:** ROWID tiebreaker on jo lisätty:

```python
ORDER BY created_at DESC, ROWID DESC
```

### Debug Mode

```python
# Lisää loggeria
from loguru import logger

logger.add("debug.log", level="DEBUG")

# Tracker logittaa automaattisesti
tracker.save_word_frequency_analysis(...)
# Log: "Saved word frequency analysis: a3b4c5d6"
```

---

## Yhteenveto

### Avainasiat:

1. **JSON = Datan serialisointi**

   - Pythonin objektit → String (tallennukseen)
   - String → Pythonin objektit (luvussa)

2. **JOIN = Yhdistä taulut**

   - Metadata (history) + Tulokset (results)
   - LEFT JOIN = Kaikki history-rivit, vaikka ei results

3. **Set-operaatiot = Vertailu**

   - Intersection (&) = Yhteiset
   - Difference (-) = Uniikit

4. **Dynaaminen SQL = Joustavuus**

   - Rakenna query tarpeen mukaan
   - Parametrit estävät SQL-injektion

5. **ROWID = Järjestyksen varmistus**
   - Kun timestamp ei riitä
   - SQLiten sisäinen rivijärjestysnumero

---

## Testikattavuus

✅ **31/31 testiä läpäistiin**

- TestSaveWordFrequencyAnalysis (8 testiä)
- TestSavePhraseAnalysis (5 testiä)
- TestGetAnalysisHistory (5 testiä)
- TestGetAnalysisResults (4 testiä)
- TestCompareAnalyses (5 testiä)
- TestEdgeCases (4 testiä)

**Testatut skenaariot:**

- ✅ Normaalit käyttötapaukset
- ✅ Suodattimet ja rajoittimet
- ✅ JSON serialisointi/deserialisointi
- ✅ Virhetilanteet (NULL, tyhjät listat, invalid ID)
- ✅ Erikoismerkit ja Unicode
- ✅ Suuret datasetit (1000+ sanaa)

---

**Viimeksi päivitetty:** 2026-01-15  
**Tekijä:** AI Assistant + vvirtai  
**Tiedosto:** `app/analytics/analysis_tracker.py`
