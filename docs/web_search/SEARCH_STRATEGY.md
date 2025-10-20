# Web Search Strategy

## Overview

Hệ thống tìm kiếm web của brandmind-ai sử dụng **SearXNG + Bing fallback** với global throttling để tránh bị rate-limit từ các search engines.

## Architecture

```
┌─────────────┐
│  Agent API  │
│ search_web()│
└──────┬──────┘
       │
       ├─ Global Throttle (2.5s delay between all requests)
       ├─ Query Deduplication
       ├─ Per-Engine Circuit Breaker (3 failures → 60s disable)
       │
       └─► SearXNG (port 8080)
            │ (Primary: duckduckgo → brave → startpage → Swisscows → google)
            │
            ├─ Engine 1: DuckDuckGo
            ├─ Engine 2: Brave ✅ (Most reliable)
            ├─ Engine 3: StartPage
            ├─ Engine 4: Swisscows
            └─ Engine 5: Google (Last resort)
                 │
                 └─ All fail? → Fallback to Bing direct search
                      │
                      └─► bing_web_search()
                           ├─ Language detection (Vietnamese vs English)
                           ├─ Vietnamese: locale params (mkt=vi-VN, setlang=vi, cc=VN)
                           └─ English: auto-detect via Accept-Language header
```

## Three Search Functions

### 1. `search_web()` - RECOMMENDED (SearXNG + Bing Fallback)
**Pros:**
- ✅ Multi-engine fallback (DuckDuckGo → Brave → StartPage → Swisscows → Google)
- ✅ Automatic fallback to Bing if all SearXNG engines fail
- ✅ Vietnamese & English language-aware search
- ✅ Global throttle prevents rate-limiting (2.5s minimum delay)
- ✅ Per-engine circuit breaker (disable for 60s after 3 failures)
- ✅ Query deduplication
- ✅ Parallel execution (2 workers max)

**Cons:**
- ⚠️ Depends on SearXNG service running (for primary searches)
- ⚠️ Bing fallback may have fewer results for certain queries

**Usage:**
```python
from shared.agent_tools.search_web import search_web

# English queries
results = search_web(["python tutorial", "machine learning"], top_k=5)

# Vietnamese queries
results = search_web(["cách làm phở bò", "bánh mì Việt Nam"], top_k=5)

# Mixed queries
results = search_web(
    ["how to cook pho", "cách nấu phở bò", "coffee machine reviews"],
    top_k=3
)
```

**Response Structure:**
```python
{
    "queries": {
        "query_string": {
            "results": [SearchResult(title, url, snippet), ...],
            "result_count": 3,
            "engine_used": "brave",  # or "bing_web_search"
            "response_time": 0.65
        }
    },
    "total_execution_time": 5.41,
    "total_queries": 1,
    "average_time_per_query": 5.41
}
```

### 2. `bing_web_search()` - Direct Bing (Fallback)
**Pros:**
- ✅ Direct HTML parsing (no intermediary service)
- ✅ No service dependency
- ✅ Language-aware configuration (Vietnamese vs English auto-detection)
- ✅ count=50 parameter forces traditional organic results layout
- ✅ Base64 URL decoding for redirect links

**Cons:**
- ❌ Used only when SearXNG engines all fail
- ❌ Results vary by query time (Bing rotation)
- ❌ Can be rate-limited if called too frequently directly

**Usage:**
```python
from shared.agent_tools.search_web import bing_web_search

# English query (auto-detect via Accept-Language header)
results = bing_web_search("python programming tutorial", top_k=5)

# Vietnamese query (explicit locale params)
results = bing_web_search("cách làm phở bò", top_k=5)
```

**Language Detection:**
- Checks for Vietnamese Unicode ranges (ả, ơ, ư, etc.)
- Vietnamese: Uses `mkt=vi-VN, setlang=vi, cc=VN`
- English: Strips locale params, relies on Accept-Language header for better results

### 3. `deep_serp_search()` - Google via Scrapeless API
**Pros:**
- ✅ Google's official results
- ✅ Premium accuracy

**Cons:**
- ❌ Requires API key (paid service)
- ❌ Rate limited by provider

**Usage:**
```python
from shared.agent_tools.search_web import deep_serp_search

results = deep_serp_search("cách làm phở bò", number_of_results=5)
```

## Rate Limiting Strategy

### Global Throttle (Main Layer)

```python
_SEARXNG_THROTTLE_LOCK = threading.Lock()
_MIN_DELAY_BETWEEN_SEARXNG = 2.5  # seconds
_LAST_SEARXNG_TIME = 0.0
```

**Mechanism:**
- Serializes all SearXNG requests using a global threading lock
- Enforces minimum 2.5 second delay between any two requests
- Adds 0-0.2 second jitter for natural behavior

### Per-Engine Circuit Breaker

```python
FAILURE_THRESHOLD = 3
COOL_DOWN_SECONDS = 60
```

**Mechanism:**
- Tracks consecutive failures per engine
- After 3 consecutive failures → temporarily disable engine for 60 seconds
- Automatically re-enables after cooldown period

**Engine Priority Order:**
1. DuckDuckGo
2. Brave ✅ (Most reliable in tests)
3. StartPage
4. Swisscows
5. Google (Last resort)

### Query Deduplication

```python
# Input
queries = ["python tutorial", "machine learning", "python tutorial"]

# Processed (duplicates removed internally)
# Only 2 unique queries executed
```

**Example:**
```python
queries = [
    "cách làm phở bò",
    "bánh mì Việt Nam",
    "cách làm phở bò",  # Duplicate - will be removed
]

# Only 2 unique queries will be executed
result = search_web(queries)
```

## Performance Characteristics

### Test Results (October 2025)

| Query | Engine | Results | Time | Notes |
|-------|--------|---------|------|-------|
| "python programming tutorial" | Brave | 21 | 0.69s | ✅ English |
| "best restaurants nyc" | Brave | 1 | 0.63s | ✅ English |
| "weather forecast tomorrow" | Brave | 25 | 0.68s | ✅ English |
| "coffee machine reviews" | Brave | 23 | 0.75s | ✅ English |
| "cách nấu phở bò" | Brave | 3 | 0.69s | ✅ Vietnamese |

### Per-Query Breakdown (3 queries total)

| Metric | Value |
|--------|-------|
| Total execution time | ~16.2s |
| Average per query | ~5.4s |
| Global throttle delay | ~2.5-2.7s × 3 = ~7.5-8s |
| Actual search time | ~0.6-0.7s × 3 = ~2.0s |
| Overhead | ~5.2s (throttle + parallel execution) |
| Max parallel workers | 2 |
| Bing count parameter | 50 (force traditional results) |
| Bing timeout | 30s |

## Best Practices

### ✅ DO

1. **Use `search_web()` as default** for any search needs
   ```python
   # Good - handles everything automatically
   results = search_web(["query1", "query2"])
   ```

2. **Batch queries together** to maximize efficiency
   ```python
   # Good - 2 parallel workers with global throttle
   results = search_web(["q1", "q2", "q3", "q4"], top_k=5)
   
   # Avoid - sequential calls without deduplication benefits
   r1 = search_web(["q1"])
   r2 = search_web(["q2"])
   r3 = search_web(["q3"])
   ```

3. **Mix Vietnamese and English queries** in same batch
   ```python
   # Good - auto-detects language per query
   results = search_web([
       "how to cook pho",
       "cách nấu phở bò",
       "bánh mì Việt Nam"
   ])
   ```

4. **Handle Bing fallback results** gracefully
   ```python
   for query, data in results["queries"].items():
       if data["engine_used"] == "bing_web_search":
           logger.info(f"Query '{query}' fell back to Bing")
       print(f"Found {data['result_count']} results via {data['engine_used']}")
   ```

5. **Monitor global throttle impact**
   ```python
   result = search_web(queries)
   total_time = result["total_execution_time"]
   search_time = total_time - (len(queries) * 2.5)  # Subtract throttle time
   logger.info(f"Pure search time: {search_time:.2f}s (throttle overhead: {len(queries) * 2.5}s)")
   ```

### ❌ DON'T

1. **Don't call search functions in tight loops** (defeats rate limiting)
   ```python
   # Bad - high request rate
   for query in queries:
       search_web([query])  # 2.5s throttle × N queries = very slow
   
   # Good - batch together
   search_web(queries)  # 2.5s throttle × 1 = fast
   ```

2. **Don't rely on specific engine** (use fallback chain)
   ```python
   # Bad - if Google is blocked, fails completely
   # (Google is intentionally last in priority)
   
   # Good - automatic fallback
   search_web(["query"])  # Tries: DDG → Brave → StartPage → Swisscows → Google → Bing
   ```

3. **Don't ignore fallback results** - they're legitimate
   ```python
   # Anti-pattern - treating Bing results as "worse"
   if data["engine_used"] == "bing_web_search":
       skip_results = True  # ❌ Don't do this!
   
   # Better - treat results equally
   if data["result_count"] > 0:
       use_results = True  # ✅ Good
   ```

## Troubleshooting

### "No results found" on valid English queries

**Cause:** Bing's HTML layout varies - some queries return Copilot-only page without organic results

**Solution:**
```python
# search_web() handles this automatically - uses SearXNG with multiple engines
results = search_web(["your_query"], top_k=5)  # Falls back to Brave if DDG fails
```

**Technical Detail:** The `count=50` parameter in Bing URL forces traditional organic results layout instead of Copilot suggestions-only page.

### "No results found" on valid Vietnamese queries

**Cause:** SearXNG engine failing (rare), or Bing locale detection issue

**Solution:**
```python
# Use search_web() which tries multiple engines in order
results = search_web(["your_vietnamese_query"], top_k=5)

# Logs will show which engine was used
# Expected: "Engine used: brave" or "Engine used: bing_web_search"
```

### "Connection refused" to SearXNG

**Cause:** SearXNG service not running

**Solution:**
```bash
# Start SearXNG service
cd /Users/mac/projects/brandmind-ai
docker-compose -f infra/services/searxng/docker-compose.yml up -d

# Verify it's running
curl -s http://localhost:8080/health | head -20

# Check logs
docker-compose -f infra/services/searxng/docker-compose.yml logs -f searxng
```

### Rate limit / Engine circuit breaker triggered

**Symptom:** Logs show "engine X returned 0 useful results, trying next engine" repeatedly

**Cause:** Engine blocking requests temporarily (normal, expected)

**Solution:**
```python
# search_web() handles this automatically
# - Tries next engine in priority order
# - After 3 consecutive failures, temporarily disables engine for 60s
# - Automatic recovery after cooldown

# In logs you'll see:
# - "Engine duckduckgo returned 0 useful results for query"
# - "Query found 3 results using engine: brave" ✅
```

### Very slow search (>10 seconds per query)

**Cause:** Expected with global throttle (2.5s delay per request minimum)

**Details:**
- Each query waits ~2.5s for global throttle
- Plus ~0.6-0.8s for actual search
- Total ~3.1-3.3s per query minimum (with 1 worker)
- 2 parallel workers: ~1.5-1.7s per query with throttle

**Optimization:**
```python
# Batch queries to amortize throttle overhead
results = search_web(["q1", "q2", "q3", "q4"])  # Parallel with 2 workers
# Time: ~7-8s for 4 queries (~2s each)
# vs sequential: ~12-13s (3s each)

## Configuration

### Global Throttle Settings (Python)

Located in: `src/shared/src/shared/agent_tools/search_web.py`

```python
_SEARXNG_THROTTLE_LOCK = threading.Lock()
_LAST_SEARXNG_TIME = 0.0
_MIN_DELAY_BETWEEN_SEARXNG = 2.5  # seconds

# Per-engine circuit breaker
FAILURE_THRESHOLD = 3  # Disable after 3 consecutive failures
COOL_DOWN_SECONDS = 60  # Re-enable after 60 seconds
```

### SearXNG Settings

Located in: `infra/services/searxng/data/settings.yml`

**Global Timeouts:**
```yaml
outgoing:
  request_timeout: 15.0      # seconds per request
  max_request_timeout: 20.0  # absolute maximum
  pool_maxsize: 1            # serialize outgoing connections
```

**Ban Configuration:**
```yaml
ban_time_on_fail: 10                    # seconds
max_ban_time_on_fail: 120               # max ban time
suspended_times:
  SearxEngineCaptcha: 172800           # 2 days
  SearxEngineAccessDenied: 86400       # 1 day
  SearxEngineTooManyRequests: 300      # 5 minutes
```

**Engine-Specific Config (Google):**
```yaml
google:
  timeout: 15.0
  params:
    hl: "vi"
    gl: "VN"
    lr: "lang_vi"
    safe: "off"
```

### Bing Fallback Settings

Located in: `src/shared/src/shared/agent_tools/search_web.py`

```python
# Language-aware Bing parameters
if is_vietnamese:
    params = {
        "q": query,
        "mkt": "vi-VN",
        "setlang": "vi",
        "cc": "VN",
        "count": "50",  # Force traditional results layout
    }
else:
    params = {
        "q": query,
        "count": "50",  # Force traditional results layout
    }

# Accept-Language header (sent in all cases)
"Accept-Language: en-US,en;q=0.9,vi;q=0.8"

# Curl timeout
timeout=30  # seconds
```

## Monitoring

### Logging Output

All search functions provide detailed logs:

```python
from shared.agent_tools.search_web import search_web

result = search_web(["python tutorial", "machine learning"])
```

**Log Output:**
```
2025-10-20 02:00:27.455 | INFO | Starting web search for 2 queries
2025-10-20 02:00:27.955 | WARNING | Engine duckduckgo returned 0 results for "python tutorial", trying next engine
2025-10-20 02:00:27.955 | DEBUG | Global throttle: sleeping 2.580s to maintain 2.5s interval
2025-10-20 02:00:34.220 | INFO | Query "python tutorial" found 3 results using engine: brave
2025-10-20 02:00:34.220 | DEBUG | Global throttle: sleeping 2.675s to maintain 2.5s interval
2025-10-20 02:00:37.537 | INFO | Query "machine learning" found 3 results using engine: brave
2025-10-20 02:00:43.688 | INFO | Total execution time: 16.23 seconds
2025-10-20 02:00:43.688 | INFO | Average time per query: 5.41 seconds
```

### Response Metrics

Check returned `response` dict:

```python
result = search_web(["query"])

# Per query metrics
for query, data in result["queries"].items():
    print(f"Query: {query}")
    print(f"  Results: {data['result_count']}")
    print(f"  Engine: {data['engine_used']}")  # brave, bing_web_search, etc.
    print(f"  Time: {data['response_time']:.2f}s")

# Total metrics
print(f"Total time: {result['total_execution_time']:.2f}s")
print(f"Avg/query: {result['average_time_per_query']:.2f}s")

# Expected output:
# Query: python tutorial
#   Results: 3
#   Engine: brave
#   Time: 1.00s
# Total time: 5.41s
# Avg/query: 5.41s
```

### Circuit Breaker State

Monitor engine health:

```python
# Logs will indicate:
# - Which engines are working: "Query found X results using engine: Y"
# - Which engines are down: "Engine X returned 0 useful results"
# - When fallback triggers: "Query found X results using engine: bing_web_search"

# After 3 consecutive failures:
# - Engine is disabled for 60 seconds
# - Next query automatically tries next engine
# - After 60s, disabled engine re-enabled
```

## Future Improvements

- [x] ✅ Global throttle (implemented: 2.5s minimum delay)
- [x] ✅ Per-engine circuit breaker (implemented: 3 failures → 60s disable)
- [x] ✅ Bing fallback (implemented: language-aware with count=50)
- [x] ✅ Query deduplication (implemented: removes duplicates before search)
- [x] ✅ Multi-engine support (implemented: 5 engines with priority order)
- [ ] Redis cache for query results (TTL: 24h) - future enhancement
- [ ] Request queue with priority (urgent vs background) - future enhancement
- [ ] Machine learning for result ranking - future enhancement
- [ ] Metrics dashboard / visualization - future enhancement
- [ ] A/B testing framework for engine combinations - future enhancement

## Recent Changes (October 2025)

### Added
- ✅ `count=50` parameter to Bing fallback (forces traditional results layout)
- ✅ Language-aware Bing configuration (Vietnamese vs English auto-detection)
- ✅ Global throttle with 2.5s minimum delay between all requests
- ✅ Per-engine circuit breaker (disable after 3 failures for 60s)

### Fixed
- ✅ Bing fallback was returning 0 results for some English queries
- ✅ Removed unused SearXNG plugin (global_throttle.py)
- ✅ Improved HTML parsing robustness with count=50 parameter

### Test Results
- 100% success rate on diverse query types (English + Vietnamese)
- Average 0.6-0.7s per actual search (excluding throttle)
- Global throttle maintained at 2.5-2.7s intervals consistently
