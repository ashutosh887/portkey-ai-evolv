# Deduplication Implementation Guide

## Overview - Production-Grade Stack

| Purpose | Technique | Notes |
|---------|-----------|-------|
| Exact duplicates | **SHA-256** | Fast, reliable |
| Near-duplicates | **SimHash** | Google-style, 64-bit fingerprint |
| Similarity measure | **Hamming Distance** | Count differing bits |

---

## Architecture

```
Incoming Prompt
      ↓
  Normalize (lowercase, remove punctuation)
      ↓
  SHA256 Hash → DB check (exact dedup)
      ↓
  SimHash → Hamming distance check (near dedup)
      ↓
  If similar → SKIP + LOG
  Else → STORE
```

---

## 1. Text Normalization

```python
def normalize_text(text: str) -> str:
    text = text.lower()                    # "Hello World" → "hello world"
    text = re.sub(r'[^\w\s]', '', text)    # Remove punctuation
    text = re.sub(r'\s+', ' ', text)       # Collapse whitespace
    return text.strip()
```

---

## 2. Hash-based Exact Dedup (SHA-256)

```python
def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
```

| Prompt | Hash |
|--------|------|
| "hello world" | `b94d27b9...` |
| "hello world" | `b94d27b9...` ← **Same = duplicate** |

---

## 3. SimHash Algorithm (Google-style)

### Key Insight
> Similar texts → hashes differ in **few bits**

```
Text A → 1010110010101100
Text B → 1010110010101110
                      ↑
Only 1 bit different → very similar!
```

### How SimHash Works

**Step 1:** Split text into tokens (words)
```
"i need help writing code" → ["i", "need", "help", "writing", "code"]
```

**Step 2:** Hash each token to 64 bits
```
"need"   → 1001011...  (64 bits)
"help"   → 0110100...  (64 bits)
"writing"→ 1100010...  (64 bits)
```

**Step 3:** Build weighted vector
- For each bit position, accumulate +1 (if bit=1) or -1 (if bit=0)

**Step 4:** Final fingerprint
- If sum > 0 → bit = 1
- If sum ≤ 0 → bit = 0

### Result
```python
simhash("i need help writing code")    → 0x7A3F1B2C...
simhash("i need help with writing code") → 0x7A3F1B2E...
                                                    ↑
                                        Only 2 bits differ!
```

---

## 4. Hamming Distance

Counts how many bits differ between two hashes:

```python
def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")
```

### Thresholds

| Distance | Similarity | Action |
|----------|------------|--------|
| 0-3 bits | ~98%+ | **Skip as duplicate** |
| 4-8 bits | ~90%+ | Very similar |
| 9-15 bits | Loosely similar | Keep |
| 16+ bits | Different | Keep |

---

## Practical Examples

### Example 1: Exact Match (SHA-256 catches)
```
"Write a Python function"
"Write a Python function"
→ Same SHA-256 hash → SKIPPED
```

### Example 2: Near-Duplicate (SimHash catches)
```
"I need help writing code"
"I need help with writing code"
→ SimHash distance = 2 bits → LOGGED & SKIPPED
```

### Example 3: Different Prompts (Saved)
```
"Explain machine learning"
"How to cook pasta"
→ SimHash distance = 28 bits → BOTH SAVED
```

---

## CLI Commands

**Start Worker:**
```cmd
python -m apps.cli.main portkey-worker --interval 10
```

**View Prompts:**
```cmd
python -m apps.cli.main prompts
```

**Expected Logs:**
```
Processing 377 logs with deduplication...
Loaded 500 existing prompts into SimHash index
Near-duplicate (Hamming=2): 'hello how are you...' matches abc123
Deduplication complete: 50 saved, 200 exact duplicates, 127 near-duplicates skipped
```

---

## Why SimHash over MinHash+LSH?

| Feature | SimHash | MinHash+LSH |
|---------|---------|-------------|
| Complexity | Simple | Complex |
| Dependencies | None (pure Python) | datasketch library |
| Storage | 64 bits per text | ~128-512 bytes |
| Speed | O(n) comparison | O(1) with index |
| Best for | Text fingerprinting | Set similarity |

**SimHash wins for production prompt dedup:**
- Simpler code
- No dependencies
- Easy to store in DB
- Battle-tested (Google uses it)
