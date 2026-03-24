# Task 36: search_places Tool — Google Places API Integration

## 📌 Metadata

- **Epic**: Brand Strategy — Tools
- **Priority**: High
- **Estimated Effort**: 1 week
- **Team**: Backend
- **Related Tasks**: Task 29 (Search Orchestration), Task 34 (Browser Tool)
- **Blocking**: Task 40 (analyze_reviews depends on search_places), Task 43 (Market Research Skill)
- **Blocked by**: None

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [x] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [x] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] ✅ [Component 1: Google Places API Client](#component-1-google-places-api-client) - REST API wrapper
    - [x] ✅ [Component 2: search_places Function](#component-2-search_places-function) - Tool function
    - [x] ✅ [Component 3: Response Formatter](#component-3-response-formatter) - Structured output formatting
    - [x] ✅ [Component 4: Configuration & API Key Management](#component-4-configuration--api-key-management) - Config integration
- [ ] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation (needs GOOGLE_PLACES_API_KEY)
- [ ] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards with comprehensive documentation
- **Blueprint Reference**: `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — Section 5.3, Tool 8
- **Google Places API (New)**: https://developers.google.com/maps/documentation/places/web-service/text-search
- **Pricing**: $0.04/request, $200/mo free credit → ~5,000 free requests/month
- **Existing search pattern**: `src/shared/src/shared/agent_tools/search/` — provider architecture reference

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Brand strategy Phase 1 cần **local competitor mapping** — tìm và phân tích các đối thủ cạnh tranh trong khu vực
- Hiện tại agent chỉ có `search_web` (general web search) và `crawl_web` (page extraction) — không có khả năng tìm kiếm cụ thể theo **vị trí địa lý**
- F&B business cạnh tranh **chủ yếu theo địa phương** (bán kính 2-5km) — cần biết chính xác ai đang kinh doanh gì, ở đâu, rating bao nhiêu
- Google Places API (New) cung cấp: tên, địa chỉ, rating, số lượng review, price level, giờ mở cửa, reviews, website, loại hình (dine-in, delivery, takeout)
- API cũng cần cho Phase 0.5 (Brand Equity Audit — kiểm tra brand hiện tại trên Google Maps)

### Mục tiêu

Xây dựng `search_places` tool cho phép agent:

1. Tìm kiếm businesses theo query + location + radius
2. Nhận kết quả đầy đủ bao gồm rating, reviews, pricing level
3. Thu thập review summaries để hiểu perception của khách hàng
4. Hỗ trợ competitive landscape mapping cho Phase 1

### Success Metrics / Acceptance Criteria

- **Functionality**: Agent gọi `search_places("specialty coffee", "District 1, HCMC")` → nhận danh sách 10-20 quán với đầy đủ thông tin
- **Data Richness**: Mỗi kết quả có: name, address, rating, review count, price level, reviews snippet
- **Error Handling**: Graceful fallback khi API key hết quota hoặc invalid
- **Cost Efficiency**: Sử dụng FieldMask để chỉ request fields cần thiết
- **Vietnam Support**: Hoạt động tốt với Vietnamese addresses và business names

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Google Places API (New) Text Search**: Sử dụng `POST /v1/places:searchText` endpoint với location bias. REST client thuần (requests/httpx), không dùng Google SDK nặng. Follow existing search provider pattern.

### Stack công nghệ

- **httpx**: Async HTTP client (đã có trong project dependencies qua crawl4ai)
- **Google Places API (New)**: `places.googleapis.com/v1/places:searchText`
- **Pydantic**: Response models

### Issues & Solutions

1. **Location geocoding** → Two-tier strategy: (a) `VIETNAM_CITIES` dict for fast coordinate lookup of common cities/districts, (b) if location not in dict → append location text to search query instead of using `locationBias`. Google Places Text Search understands natural language location references (e.g., "specialty coffee Quận 5 HCMC"). No Geocoding API needed — reduces cost and complexity
2. **Rate limiting** → Respect 600 QPM limit; implement simple rate limiter
3. **Cost control** → FieldMask limits response fields → reduces cost per request
4. **Vietnamese text** → API supports `languageCode: "vi"` for Vietnamese results
5. **Reviews in FIELD_MASK** → Including `places.reviews` in Text Search FIELD_MASK pushes the request to Pro SKU ($0.035/req vs $0.0065 Basic). However, the alternative (Basic Text Search + separate Place Details per result) is **more expensive** ($0.0065 + N × $0.04 = $0.207 for 5 results) and returns reviews for fewer results. Decision: **include `places.reviews` in FIELD_MASK** — single Pro request ($0.035) gives reviews for all results. `get_place_details()` is kept as a separate method for on-demand use (e.g., `analyze_reviews` in Task 40 needs full detail for a specific business).
6. **Sync client** → `GooglePlacesClient` uses `httpx.Client` (sync) directly — simpler than async, avoids event loop issues, matches codebase tool convention (`search_web`, `scrape_web_content` are all sync).

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: API Client & Core Logic**
1. **Google Places Client**
   - Implement async REST client for Places API (New)
   - Text Search with location bias
   - FieldMask optimization for F&B-relevant fields
   - *Decision Point: Verify API key setup with GCP project*

2. **Response Parsing**
   - Parse Places API JSON response into Pydantic models
   - Extract: name, address, rating, reviewCount, priceLevel, reviews, hours, website

### **Phase 2: Tool Integration & Formatting**
1. **Tool Function**
   - Create `search_places` plain function following existing patterns (`search_web`, `scrape_web_content`)
   - Format results into agent-readable markdown

2. **Config & Registration**
   - Add GOOGLE_PLACES_API_KEY to config system
   - Register tool for agent discovery via tool_search

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards & Documentation Requirements**
>
> All code implementations **MUST** follow **enterprise-level Python standards** with comprehensive docstrings, type hints, double quotes, max 100 char lines, English only.

### Component 1: Google Places API Client

#### Requirement 1 - Async REST Client for Places Text Search
- **Requirement**: Build async client wrapper for Google Places API (New) Text Search endpoint
- **Implementation**:
  - `src/shared/src/shared/agent_tools/places/places_client.py`
  ```python
  import unicodedata

  import httpx
  from pydantic import BaseModel, Field


  class PlaceReview(BaseModel):
      """A single user review for a place."""
      author: str = ""
      rating: int = 0
      text: str = ""
      relative_time: str = ""


  class PlaceResult(BaseModel):
      """Structured result for a single place from Google Places API."""
      place_id: str
      name: str
      address: str = ""
      rating: float | None = None
      review_count: int = 0
      price_level: str | None = None  # PRICE_LEVEL_FREE to PRICE_LEVEL_VERY_EXPENSIVE
      website: str | None = None
      phone: str | None = None
      opening_hours: list[str] = Field(default_factory=list)
      dine_in: bool | None = None
      delivery: bool | None = None
      takeout: bool | None = None
      reviews: list[PlaceReview] = Field(default_factory=list)
      types: list[str] = Field(default_factory=list)
      google_maps_url: str | None = None


  # Major Vietnamese city coordinates for locationBias optimization.
  # City-level only — districts/wards are NOT hardcoded here.
  # When location is a district (e.g., "Quận 1"), _resolve_location
  # returns None → text_search appends location to query text instead.
  # Google Places API understands "coffee Quận 1 HCMC" natively.
  #
  # Keys: normalized lowercase, no diacritics. Multiple aliases per city.
  # Coordinates: verified via latlong.net, latitude.to (2026-03-10).
  VIETNAM_CITIES: dict[str, tuple[float, float]] = {
      # Ho Chi Minh City
      "ho chi minh": (10.7769, 106.7009),
      "hcmc": (10.7769, 106.7009),
      "tp hcm": (10.7769, 106.7009),
      "sai gon": (10.7769, 106.7009),
      # Hanoi
      "hanoi": (21.0285, 105.8542),
      "ha noi": (21.0285, 105.8542),
      # Major cities
      "da nang": (16.0544, 108.2022),
      "hai phong": (20.8449, 106.6881),
      "can tho": (10.0452, 105.7469),
      "nha trang": (12.2451, 109.1943),
      "hue": (16.4637, 107.5909),
      "vung tau": (10.3460, 107.0843),
      "da lat": (11.9465, 108.4419),
      "quy nhon": (13.7830, 109.2197),
      "buon ma thuot": (12.6680, 108.0378),
      "phu quoc": (10.2899, 103.9840),
      "bien hoa": (10.9574, 106.8426),
      "thu dau mot": (11.0036, 106.6520),
      "long xuyen": (10.3860, 105.4350),
      "rach gia": (10.0125, 105.0809),
      "ha long": (20.9517, 107.0845),
  }


  class GooglePlacesClient:
      """
      Async REST client for Google Places API (New).

      Implements the Text Search endpoint to find local businesses
      by query and location. Optimized for F&B competitive landscape
      mapping with FieldMask to minimize cost per request.

      Attributes:
          api_key: Google Cloud API key with Places API enabled
          base_url: Places API base URL
      """

      FIELD_MASK = ",".join([
          "places.id",
          "places.displayName",
          "places.formattedAddress",
          "places.rating",
          "places.userRatingCount",
          "places.priceLevel",
          "places.reviews",
          "places.regularOpeningHours",
          "places.websiteUri",
          "places.nationalPhoneNumber",
          "places.delivery",
          "places.dineIn",
          "places.takeout",
          "places.types",
          "places.googleMapsUri",
      ])
      # Including places.reviews pushes Text Search to Pro SKU ($0.035/req).
      # This is intentional — a single Pro request is much cheaper than
      # Basic ($0.0065) + N × Place Details ($0.04 each) to fetch reviews
      # separately, and gives reviews for ALL results, not just top N.

      def __init__(self, api_key: str):
          """Initialize with Google Cloud API key."""
          self._api_key = api_key
          self._client = httpx.Client(timeout=30.0)

      def text_search(
          self,
          query: str,
          location: str | None = None,
          radius_meters: int = 5000,
          max_results: int = 20,
          language: str = "vi",
      ) -> list[PlaceResult]:
          """
          Search for places via Google Places Text Search API.

          If location resolves to coordinates, uses locationBias.
          Otherwise appends location text to query for natural matching.

          Args:
              query: Search text (e.g., "specialty coffee shop")
              location: Location name (e.g., "Da Nang", "Quận 1 HCMC")
              radius_meters: Search radius in meters (default 5km)
              max_results: Maximum results (max 20)
              language: Language code (default "vi")

          Returns:
              List of PlaceResult with business details.
          """
          url = "https://places.googleapis.com/v1/places:searchText"
          headers = {
              "Content-Type": "application/json",
              "X-Goog-Api-Key": self._api_key,
              "X-Goog-FieldMask": self.FIELD_MASK,
          }

          # Resolve location → coordinates or fallback to query text
          body: dict = {
              "textQuery": query,
              "maxResultCount": max(1, min(max_results, 20)),
              "languageCode": language,
          }

          if location:
              coords = self._resolve_location(location)
              if coords:
                  body["locationBias"] = {
                      "circle": {
                          "center": {
                              "latitude": coords[0],
                              "longitude": coords[1],
                          },
                          "radius": float(radius_meters),
                      }
                  }
              else:
                  # Location not in dict → append to query text
                  body["textQuery"] = f"{query} {location}"

          response = self._client.post(url, headers=headers, json=body)
          response.raise_for_status()

          data = response.json()
          places_raw = data.get("places", [])
          return [self._parse_place(p) for p in places_raw]

      def _resolve_location(
          self, location: str
      ) -> tuple[float, float] | None:
          """
          Resolve location name to lat/lng via VIETNAM_CITIES lookup.

          Normalizes input (lowercase, strip diacritics) then checks dict.
          Returns None if not found — caller appends location to query text.

          Args:
              location: Location name (e.g., "Da Nang", "HCMC")

          Returns:
              (lat, lng) tuple or None if not in VIETNAM_CITIES.
          """
          # Normalize: lowercase, strip diacritics
          normalized = location.lower().strip()
          nfkd = unicodedata.normalize("NFKD", normalized)
          ascii_key = "".join(
              c for c in nfkd if not unicodedata.combining(c)
          )

          # Direct lookup
          if ascii_key in VIETNAM_CITIES:
              return VIETNAM_CITIES[ascii_key]

          # Try without common prefixes: "thanh pho", "tp", "city of"
          for prefix in ("thanh pho ", "tp ", "city of "):
              stripped = ascii_key.removeprefix(prefix)
              if stripped in VIETNAM_CITIES:
                  return VIETNAM_CITIES[stripped]

          # Try without common suffixes: "city", "province"
          for suffix in (" city", " province"):
              stripped = ascii_key.removesuffix(suffix)
              if stripped in VIETNAM_CITIES:
                  return VIETNAM_CITIES[stripped]

          # Try matching any comma-separated segment
          if "," in ascii_key:
              for segment in ascii_key.split(","):
                  segment = segment.strip()
                  if segment in VIETNAM_CITIES:
                      return VIETNAM_CITIES[segment]

          return None

      def get_place_details(
          self,
          place_id: str,
          language: str = "vi",
      ) -> PlaceResult:
          """
          Fetch full details for a single place by place_id.

          Use this for on-demand enrichment when you need complete data
          for a specific business (e.g., analyze_reviews for one competitor).
          NOT needed for general search — text_search() already includes
          reviews in its FIELD_MASK.

          Args:
              place_id: Google Place ID (from text_search results)
              language: Language code (default "vi")

          Returns:
              PlaceResult with full detail data.
          """
          detail_mask = ",".join([
              "id", "displayName", "formattedAddress", "rating",
              "userRatingCount", "priceLevel", "reviews",
              "currentOpeningHours", "websiteUri",
              "nationalPhoneNumber", "delivery", "dineIn",
              "takeout", "types", "googleMapsUri",
          ])
          url = f"https://places.googleapis.com/v1/places/{place_id}"
          headers = {
              "X-Goog-Api-Key": self._api_key,
              "X-Goog-FieldMask": detail_mask,
          }
          params = {"languageCode": language}

          response = self._client.get(url, headers=headers, params=params)
          response.raise_for_status()
          return self._parse_place(response.json())

      def _parse_place(self, raw: dict) -> PlaceResult:
          """Parse a single place from API response JSON."""
          reviews = []
          for r in raw.get("reviews", []):
              reviews.append(PlaceReview(
                  author=r.get("authorAttribution", {}).get(
                      "displayName", ""
                  ),
                  rating=r.get("rating", 0),
                  text=r.get("text", {}).get("text", ""),
                  relative_time=r.get("relativePublishTimeDescription", ""),
              ))

          # Parse opening hours — prefer regularOpeningHours (weekly schedule)
          hours_data = (
              raw.get("regularOpeningHours")
              or raw.get("currentOpeningHours")
              or {}
          )
          hours = hours_data.get("weekdayDescriptions", [])

          return PlaceResult(
              place_id=raw.get("id", ""),
              name=raw.get("displayName", {}).get("text", ""),
              address=raw.get("formattedAddress", ""),
              rating=raw.get("rating"),
              review_count=raw.get("userRatingCount", 0),
              price_level=raw.get("priceLevel"),
              website=raw.get("websiteUri"),
              phone=raw.get("nationalPhoneNumber"),
              opening_hours=hours,
              dine_in=raw.get("dineIn"),
              delivery=raw.get("delivery"),
              takeout=raw.get("takeout"),
              reviews=reviews,
              types=raw.get("types", []),
              google_maps_url=raw.get("googleMapsUri"),
          )
  ```

  **Implementation Note — Sync Tool Wrapper Pattern**:
  Since codebase tools are **sync functions** (e.g., `search_web`, `scrape_web_content`), but `GooglePlacesClient` uses async httpx, the tool function should either:

  **Option A (Recommended — already implemented above)**: Use `httpx.Client` (sync) directly in the client — simpler, avoids event loop issues:
  ```python
  class GooglePlacesClient:
      def __init__(self, api_key: str):
          self._client = httpx.Client(timeout=30.0)
          self._api_key = api_key

      def text_search(self, query: str, ...) -> list[PlaceResult]:
          response = self._client.post(url, headers=headers, json=body)
          ...
  ```

  **Option B**: Keep async client, use `asyncio.run()` in the sync wrapper — but guard against nested event loops:
  ```python
  def search_places(...) -> str:
      try:
          loop = asyncio.get_running_loop()
          # Already in async context — use nest_asyncio or thread
          import nest_asyncio
          nest_asyncio.apply()
          return loop.run_until_complete(_async_search_places(...))
      except RuntimeError:
          return asyncio.run(_async_search_places(...))
  ```
- **Acceptance Criteria**:
  - [ ] Successfully calls Places API Text Search endpoint
  - [ ] Parses all relevant fields from response
  - [ ] Location resolution works for major VN cities/districts
  - [ ] Handles API errors (401, 429, 500) gracefully

### Component 2: search_places Function

#### Requirement 1 - Plain Function Interface
- **Requirement**: Create `search_places` as a plain function callable by the agent. Follows codebase convention — `search_web` and `scrape_web_content` are both plain functions, `create_agent()` accepts them directly.
- **Implementation**:
  - `src/shared/src/shared/agent_tools/places/search_places.py`
  ```python
  from loguru import logger

  from config.system_config import SETTINGS
  from shared.agent_tools.places.formatter import format_places_markdown
  from shared.agent_tools.places.places_client import GooglePlacesClient


  def search_places(
      query: str,
      location: str | None = None,
      radius_meters: int = 5000,
      max_results: int = 20,
  ) -> str:
      """
      Search for local businesses using Google Places API.

      Use this tool to find competitors, map the local F&B market,
      and understand the competitive landscape in a specific area.
      Returns business details including name, address, rating,
      reviews, pricing level, and opening hours.

      Best for: local competitor mapping, finding nearby businesses,
      getting review data for F&B establishments.

      Args:
          query: Search query (e.g., "specialty coffee shop",
              "quán cà phê đặc sản")
          location: Location center for search
              (e.g., "District 1, Ho Chi Minh City")
          radius_meters: Search radius in meters (default 5000 = 5km)
          max_results: Maximum number of results (default 20, max 20)

      Returns:
          Formatted markdown with business details: name, address,
          rating, review count, price level, reviews summary.
          Returns error message string if API call fails.
      """
      api_key = SETTINGS.GOOGLE_PLACES_API_KEY
      if not api_key:
          return (
              "Google Places API key not configured. "
              "Please add GOOGLE_PLACES_API_KEY to your .env file."
          )

      try:
          client = GooglePlacesClient(api_key=api_key)
          results = client.text_search(
              query=query,
              location=location,
              radius_meters=radius_meters,
              max_results=max_results,
          )

          if not results:
              return f"No results found for '{query}' in {location or 'any location'}."

          # Reviews are included in text_search() FIELD_MASK (Pro SKU).
          # No separate Place Details calls needed — all results have reviews.
          return format_places_markdown(results, query, location)

      except Exception as e:
          logger.error(f"search_places failed: {e}")
          return f"Places search failed: {e}"
  ```
- **Acceptance Criteria**:
  - [ ] Tool is discoverable via `tool_search`
  - [ ] Returns well-formatted markdown for agent consumption
  - [ ] Handles missing API key with clear error message

### Component 3: Response Formatter

#### Requirement 1 - Markdown Formatting for Agent
- **Requirement**: Format PlaceResult list into agent-readable markdown
- **Implementation**:
  - `src/shared/src/shared/agent_tools/places/formatter.py`
  - Produces structured markdown per place: name, rating stars, address, price level, top reviews, hours
  - Groups results with headers and separators
- **Acceptance Criteria**:
  - [ ] Output is clean, readable markdown
  - [ ] Rating displayed as stars (★★★★☆)
  - [ ] Reviews truncated to reasonable length

### Component 4: Configuration & API Key Management

#### Requirement 1 - Add GOOGLE_PLACES_API_KEY to Config
- **Requirement**: Integrate API key into existing config system
- **Implementation**:
  - Add `GOOGLE_PLACES_API_KEY` to `src/config/system_config.py`
  - Add to `.env.example`
  - Validate key presence on tool initialization
- **Acceptance Criteria**:
  - [ ] API key loaded from environment variable
  - [ ] Clear error message if key is missing when tool is called
  - [ ] Works with existing config system

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Basic Text Search
- **Purpose**: Verify tool returns results for a standard F&B query
- **Steps**:
  1. Call `search_places("specialty coffee", "District 1, HCMC")`
  2. Verify results are returned
  3. Check each result has name, address, rating
- **Expected Result**: 5-20 coffee shop results with complete details
- **Status**: ⏳ Pending

### Test Case 2: Location Resolution
- **Purpose**: Verify Vietnamese location names resolve correctly
- **Steps**:
  1. Test "District 1, HCMC" → coordinates near 10.77, 106.70
  2. Test "Quận 3" → coordinates near 10.78, 106.69
  3. Test "Hà Nội" → coordinates near 21.03, 105.85
- **Expected Result**: All locations resolve to correct coordinates
- **Status**: ⏳ Pending

### Test Case 3: Error Handling — No API Key
- **Purpose**: Verify graceful degradation without API key
- **Steps**:
  1. Remove GOOGLE_PLACES_API_KEY from config
  2. Call search_places
- **Expected Result**: Clear message: "Google Places API key not configured. Please add GOOGLE_PLACES_API_KEY to your .env file."
- **Status**: ⏳ Pending

### Test Case 4: Review Data Extraction
- **Purpose**: Verify review content is included in results
- **Steps**:
  1. Call search_places for a well-known café chain
  2. Check reviews field in response
- **Expected Result**: At least some results include review snippets
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation.

### What Was Implemented

**Components Completed**:
- [ ] [Component 1]: Google Places API Client
- [ ] [Component 2]: search_places Function
- [ ] [Component 3]: Response Formatter
- [ ] [Component 4]: Configuration & API Key Management

**Files Created/Modified**:
```
src/shared/src/shared/agent_tools/places/
├── __init__.py                    # Package exports
├── places_client.py               # Google Places API REST client
├── search_places.py               # Tool function
└── formatter.py                   # Markdown response formatting

src/config/system_config.py        # Added GOOGLE_PLACES_API_KEY
```

------------------------------------------------------------------------
