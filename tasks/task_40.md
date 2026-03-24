# Task 40: Utility Analysis Tools — Reviews, Social Profile, Autocomplete

## 📌 Metadata

- **Epic**: Brand Strategy — Tools
- **Priority**: Medium (P2 — analyze_reviews; P2 — analyze_social_profile; P3 — get_search_autocomplete)
- **Estimated Effort**: 1 week
- **Team**: Backend
- **Related Tasks**: Task 36 (search_places — reviews data source), Task 29 (Search Orchestration)
- **Blocking**: Task 43 (Market Research Skill uses all 3 tools)
- **Blocked by**: Task 36 (search_places — for review data)

### ✅ Progress Checklist

- [x] 🎯 [Context & Goals](#🎯-context--goals)
- [x] 🛠 [Solution Design](#🛠-solution-design)
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan)
- [x] 📋 [Implementation Detail](#📋-implementation-detail)
    - [x] ✅ [Component 1: analyze_reviews Tool](#component-1-analyze_reviews-tool)
    - [x] ✅ [Component 2: analyze_social_profile Tool](#component-2-analyze_social_profile-tool)
    - [x] ✅ [Component 3: get_search_autocomplete Tool](#component-3-get_search_autocomplete-tool)
- [ ] 🧪 [Test Cases](#🧪-test-cases)
- [ ] 📝 [Task Summary](#📝-task-summary)

## 🔗 Reference Documentation

- **Blueprint Reference**: `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — Section 5.2, Tools 13-15
- **Google Places reviews**: Included in search_places response (Task 36)
- **Google Autocomplete**: `suggestqueries.google.com/complete/search?client=firefox&q={query}`
- **browse_and_research** (NOT `browse_social_media`): `src/shared/src/shared/agent_tools/browser/browser_tool.py` — factory function `create_browse_tool()` returns an async `browse_and_research(task: str) -> str` function. There is NO `browse_social_media` function in the codebase.

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Phase 1 (Market Intelligence) cần 3 analysis tools:
  - **analyze_reviews**: Tổng hợp & phân tích review từ Google Maps và social media — tìm customer sentiment patterns, unmet needs, competitor weaknesses
  - **analyze_social_profile**: Phân tích brand strategy của đối thủ qua social media profile — content strategy, engagement, visual identity, brand voice
  - **get_search_autocomplete**: Lấy Google autocomplete suggestions — hiểu người dùng đang search gì liên quan đến ngành/khu vực
- 3 tools này đều là "composite tools" — kết hợp existing tools + LLM analysis
- analyze_reviews = search_places (reviews) + Gemini (sentiment analysis)
- analyze_social_profile = browse_and_research (data) + Gemini (structured analysis)
- get_search_autocomplete = REST API (simple, no LLM)

### Mục tiêu

1. analyze_reviews: Agent phân tích được review patterns cho một business hoặc category trong khu vực
2. analyze_social_profile: Agent đánh giá được brand strategy của competitor thông qua social media
3. get_search_autocomplete: Agent khám phá được search patterns liên quan đến ngành/khu vực

### Success Metrics / Acceptance Criteria

- **analyze_reviews**: Trả về structured sentiment analysis (themes, sentiment scores, key quotes, unmet needs)
- **analyze_social_profile**: Trả về brand strategy assessment (content pillars, engagement, visual style, voice)
- **get_search_autocomplete**: Trả về 10+ autocomplete suggestions cho một query

------------------------------------------------------------------------

## 🛠 Solution Design

### Existing Components (Reuse)

| Component | Location | Reuse |
|-----------|----------|-------|
| search_places + PlaceResult | `src/shared/src/shared/agent_tools/places/` (Task 36) | Review data source |
| browse_and_research | `src/shared/src/shared/agent_tools/browser/browser_tool.py` | Browser automation — created via `create_browse_tool()` factory |
| Gemini LLM client | `src/shared/src/shared/model_clients/llm/google/` | Analysis/synthesis |

### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| analyze_reviews tool | `src/shared/src/shared/agent_tools/analysis/analyze_reviews.py` | Review sentiment analysis |
| analyze_social_profile tool | `src/shared/src/shared/agent_tools/analysis/analyze_social_profile.py` | Social brand analysis |
| get_search_autocomplete tool | `src/shared/src/shared/agent_tools/analysis/get_search_autocomplete.py` | Autocomplete suggestions |

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: get_search_autocomplete** (simplest, no dependencies)
### **Phase 2: analyze_reviews** (depends on Task 36 search_places)
### **Phase 3: analyze_social_profile** (depends on browse_and_research)

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards**: Enterprise-level Python, comprehensive docstrings, type hints.

### Component 1: analyze_reviews Tool

#### Requirement 1 - Review Aggregation + Sentiment Analysis
- **Requirement**: Aggregate reviews from search_places and analyze sentiment patterns
- **Implementation**:
  - `src/prompts/brand_strategy/analyze_reviews.py` — prompt constant
  ```python
  REVIEW_ANALYSIS_PROMPT = """
  Analyze the following customer reviews for {{business_name}}.
  Focus on identifying:
  1. Recurring positive themes (what customers love)
  2. Recurring negative themes (what customers complain about)
  3. Unmet needs (what customers wish for but isn't provided)
  4. Competitive insights (mentions of competing businesses)
  5. Key representative quotes

  Reviews:
  {{reviews_text}}

  Respond in the following JSON format:
  {
      "overall_sentiment": "positive|neutral|negative",
      "positive_themes": [{"theme": "...", "frequency": "high|medium|low"}, ...],
      "negative_themes": [{"theme": "...", "frequency": "high|medium|low"}, ...],
      "unmet_needs": ["...", "..."],
      "competitive_insights": ["...", "..."],
      "key_quotes": ["...", "..."]
  }
  """
  ```

  - `src/shared/src/shared/agent_tools/analysis/analyze_reviews.py` — tool + models
  ```python
  import json

  from loguru import logger

  from config.system_config import SETTINGS
  from prompts.brand_strategy.analyze_reviews import REVIEW_ANALYSIS_PROMPT
  from shared.agent_tools.places.places_client import GooglePlacesClient
  from shared.model_clients.llm.google import (
      GoogleAIClientLLM,
      GoogleAIClientLLMConfig,
  )


  def analyze_reviews(
      business_name: str | None = None,
      query: str | None = None,
      location: str | None = None,
      max_businesses: int = 5,
  ) -> str:
      """
      Analyze customer reviews to find sentiment patterns and insights.

      Aggregates reviews from Google Maps (via search_places) and
      analyzes them using LLM for themes, sentiment, and unmet needs.

      Use this tool during Phase 1 to understand:
      - What customers love/hate about competitors
      - Unmet needs in the market (opportunity areas)
      - Service quality patterns in the area

      Args:
          business_name: Specific business to analyze (exact name).
              If None, analyzes top businesses matching query.
          query: Search query for businesses (e.g., "specialty coffee").
              Required if business_name is None.
          location: Area to search (e.g., "District 1, HCMC")
          max_businesses: Max businesses to analyze (default 5)

      Returns:
          Structured review analysis with themes, sentiment, and insights.
          Error message string if analysis fails.
      """
      if not business_name and not query:
          return "Either business_name or query must be provided."

      api_key = SETTINGS.GOOGLE_PLACES_API_KEY
      if not api_key:
          return (
              "Google Places API key not configured. "
              "Please add GOOGLE_PLACES_API_KEY to your .env file."
          )

      # Step 1: Search businesses and collect reviews
      search_query = business_name or query
      client = GooglePlacesClient(api_key=api_key)
      try:
          results = client.text_search(
              query=search_query,
              location=location,
              max_results=max_businesses,
          )
      except Exception as e:
          logger.error(f"Places search failed: {e}")
          return f"Failed to search places: {e}"

      if not results:
          return f"No results found for '{search_query}' in {location or 'any location'}."

      # Step 2: Fetch full reviews for each business
      all_reviews: list[dict] = []
      for place in results:
          if place.place_id:
              try:
                  detailed = client.get_place_details(place.place_id)
                  for review in detailed.reviews:
                      all_reviews.append({
                          "business": detailed.name,
                          "rating": review.rating,
                          "text": review.text,
                      })
              except Exception as e:
                  logger.warning(f"Failed to get details for {place.name}: {e}")

      if not all_reviews:
          return f"No reviews found for '{search_query}' in {location or 'any location'}."

      # Step 3: LLM analysis
      reviews_text = "\n".join(
          f"[{r['business']}] ({'★' * r['rating']}) {r['text']}"
          for r in all_reviews
      )

      llm = GoogleAIClientLLM(
          config=GoogleAIClientLLMConfig(
              model="gemini-2.5-flash-lite",
              api_key=SETTINGS.GEMINI_API_KEY,
              response_mime_type="application/json",
          )
      )

      prompt = (
          REVIEW_ANALYSIS_PROMPT
          .replace("{{business_name}}", search_query)
          .replace("{{reviews_text}}", reviews_text[:15000])
      )

      try:
          result = llm.complete(prompt, temperature=0.2).text
          analysis = json.loads(result.strip())
      except Exception as e:
          logger.error(f"Review analysis LLM call failed: {e}")
          return f"Review analysis failed: {e}"

      # Step 4: Format output
      lines = [
          f"## Review Analysis: {search_query}",
          f"**Reviews analyzed**: {len(all_reviews)} from {len(results)} businesses",
          f"**Overall sentiment**: {analysis.get('overall_sentiment', 'N/A')}\n",
      ]

      if analysis.get("positive_themes"):
          lines.append("### Positive Themes")
          for theme in analysis["positive_themes"]:
              if isinstance(theme, dict):
                  lines.append(f"- **{theme.get('theme', '')}**: {theme.get('frequency', '')}")
              else:
                  lines.append(f"- {theme}")

      if analysis.get("negative_themes"):
          lines.append("\n### Negative Themes")
          for theme in analysis["negative_themes"]:
              if isinstance(theme, dict):
                  lines.append(f"- **{theme.get('theme', '')}**: {theme.get('frequency', '')}")
              else:
                  lines.append(f"- {theme}")

      if analysis.get("unmet_needs"):
          lines.append("\n### Unmet Needs (Opportunities)")
          for need in analysis["unmet_needs"]:
              lines.append(f"- {need}")

      if analysis.get("key_quotes"):
          lines.append("\n### Key Quotes")
          for quote in analysis["key_quotes"][:5]:
              lines.append(f"> {quote}")

      return "\n".join(lines)
  ```
- **Implementation Logic**:
  1. If `business_name` → search_places(business_name, location) → get reviews for that business
  2. If `query` → search_places(query, location) → get top N businesses → aggregate reviews
  3. Concatenate reviews text
  4. Send to Gemini Flash with REVIEW_ANALYSIS_PROMPT
  5. Parse structured JSON response
  6. Format into readable output

- **Acceptance Criteria**:
  - [ ] Analyzes reviews from search_places data
  - [ ] Identifies positive/negative themes correctly
  - [ ] Surfaces unmet needs from review patterns
  - [ ] Works for single business or area-wide analysis

### Component 2: analyze_social_profile Tool

#### Requirement 1 - Social Media Brand Strategy Analysis
- **Requirement**: Use browse_and_research to visit a profile and analyze brand strategy
- **Implementation**:
  - `src/prompts/brand_strategy/analyze_social_profile.py` — prompt constant
  ```python
  SOCIAL_ANALYSIS_PROMPT = """
  Based on the social media profile data below, analyze the brand strategy:

  Profile Data:
  {{profile_data}}

  Provide a structured analysis covering:
  1. Content Strategy:
     - Content pillars (main content themes)
     - Content mix (photos/videos/stories/reels ratio)
     - Posting frequency estimation
  2. Brand Voice & Tone:
     - Communication style (formal/casual/playful)
     - Language used (bilingual, slang, professional)
     - Hashtag strategy
  3. Visual Identity:
     - Color palette consistency
     - Photography style (lifestyle/product/UGC)
     - Visual cohesion score (1-10)
  4. Engagement Assessment:
     - Follower count (if visible)
     - Engagement patterns (likes, comments quality)
     - Community management (response to comments)
  5. Brand Positioning Signal:
     - Inferred positioning (premium/mid/budget)
     - Target audience signal
     - Key differentiator communicated

  Respond in structured format.
  """
  ```

  - `src/shared/src/shared/agent_tools/analysis/analyze_social_profile.py` — tool function
  ```python
  import asyncio
  import json

  import asyncio
  import threading

  from loguru import logger

  from config.system_config import SETTINGS
  from prompts.brand_strategy.analyze_social_profile import (
      SOCIAL_ANALYSIS_PROMPT,
  )
  from shared.agent_tools.browser import BrowserManager, create_browse_tool
  from shared.model_clients.llm.google import (
      GoogleAIClientLLM,
      GoogleAIClientLLMConfig,
  )


  def analyze_social_profile(
      profile_url: str | None = None,
      platform: str = "instagram",
      username: str | None = None,
      analysis_depth: str = "standard",
  ) -> str:
      """
      Analyze a social media profile's brand strategy.

      Uses browser automation to visit the profile and LLM to analyze
      the brand strategy communicated through social media presence.

      Best for: competitor analysis during Phase 1, understanding
      how competing brands present themselves on social platforms.

      Args:
          profile_url: Direct URL to the profile
              (e.g., "https://instagram.com/competitor_brand")
          platform: Social platform — "instagram", "facebook", "tiktok"
          username: Username on the platform (alternative to URL)
          analysis_depth: "quick" (overview) | "standard" (detailed) |
              "comprehensive" (includes content audit of recent 20 posts)

      Returns:
          Structured brand strategy analysis of the social profile
      """
      # Step 1: Build profile URL and infer platform
      if not profile_url and not username:
          return "Either profile_url or username must be provided."

      # Infer platform from URL if provided directly
      if profile_url and not username:
          if "facebook.com" in profile_url:
              platform = "facebook"
          elif "tiktok.com" in profile_url:
              platform = "tiktok"
          elif "instagram.com" in profile_url:
              platform = "instagram"

      if not profile_url:
          url_templates = {
              "instagram": "https://www.instagram.com/{}/",
              "facebook": "https://www.facebook.com/{}/",
              "tiktok": "https://www.tiktok.com/@{}/",
          }
          template = url_templates.get(platform.lower())
          if not template:
              return f"Unsupported platform: {platform}. Use instagram, facebook, or tiktok."
          profile_url = template.format(username)

      # Step 2: Build browse task based on analysis_depth
      post_count = {"quick": 5, "standard": 10, "comprehensive": 20}.get(
          analysis_depth, 10
      )

      browse_task = (
          f"Visit {profile_url} and extract the following information:\n"
          f"1. Profile bio/description\n"
          f"2. Follower count (if visible)\n"
          f"3. The most recent {post_count} posts — for each post note:\n"
          f"   - Content type (photo/video/reel/carousel)\n"
          f"   - Caption or text (first 200 chars)\n"
          f"   - Engagement (likes, comments count if visible)\n"
          f"   - Hashtags used\n"
          f"4. Profile picture style\n"
          f"5. Overall visual theme/color palette\n"
          f"6. Any pinned/featured content\n"
          f"Summarize all findings in a structured format."
      )

      # Step 3: Call browse_and_research
      # browse_and_research is genuinely async (browser-use agent uses await).
      # Use thread-based bridge to handle nested event loops (same pattern
      # as crawl4ai_client._run_async).
      try:
          manager = BrowserManager()
          browse_fn = create_browse_tool(manager)
          coro = browse_fn(browse_task)

          # Thread-based sync→async bridge (handles nested event loops)
          try:
              loop = asyncio.get_event_loop()
              if loop.is_running():
                  result_holder = [None]
                  exc_holder = [None]

                  def _run():
                      try:
                          new_loop = asyncio.new_event_loop()
                          asyncio.set_event_loop(new_loop)
                          result_holder[0] = new_loop.run_until_complete(coro)
                          new_loop.close()
                      except Exception as e:
                          exc_holder[0] = e

                  t = threading.Thread(target=_run)
                  t.start()
                  t.join()
                  if exc_holder[0]:
                      raise exc_holder[0]
                  profile_data = result_holder[0]
              else:
                  profile_data = loop.run_until_complete(coro)
          except RuntimeError:
              profile_data = asyncio.run(coro)

      except RuntimeError as e:
          if "no valid browser session" in str(e).lower():
              return (
                  "Browser login session not found. Run "
                  "'brandmind browser setup' first to authenticate."
              )
          logger.error(f"Browser error: {e}")
          return f"Failed to browse profile: {e}"
      except Exception as e:
          logger.error(f"Browse failed for {profile_url}: {e}")
          return f"Failed to browse profile: {e}"

      if not profile_data or len(profile_data.strip()) < 50:
          return (
              f"Could not extract meaningful data from {profile_url}. "
              f"The profile may be private or the platform blocked access."
          )

      # Step 4: LLM analysis
      llm = GoogleAIClientLLM(
          config=GoogleAIClientLLMConfig(
              model="gemini-2.5-flash-lite",
              api_key=SETTINGS.GEMINI_API_KEY,
          )
      )

      prompt = SOCIAL_ANALYSIS_PROMPT.replace(
          "{{profile_data}}", profile_data[:15000]
      )

      try:
          result = llm.complete(prompt, temperature=0.3).text
      except Exception as e:
          logger.error(f"Social analysis LLM call failed: {e}")
          return f"Analysis failed: {e}"

      # Step 5: Format output
      header = f"## Social Profile Analysis: {username or profile_url}\n"
      header += f"**Platform**: {platform.capitalize()}\n"
      header += f"**Depth**: {analysis_depth}\n\n"
      return header + result
  ```
- **Implementation Logic**:
  1. Build profile URL from platform + username (or use direct URL)
  2. Call `browse_and_research` (from `create_browse_tool()` factory) with instruction to extract profile data. **NOTE**: The actual function name is `browse_and_research`, NOT `browse_social_media`. It is created via `create_browse_tool()` factory in `src/shared/src/shared/agent_tools/browser/browser_tool.py`.
  3. Parse profile data (bio, recent posts, engagement metrics)
  4. Send to Gemini with SOCIAL_ANALYSIS_PROMPT
  5. Format structured analysis

  **Architectural Note**: This tool internally calls another tool (`browse_and_research`) + an LLM. This creates a "tool calling LLM calling tool" pattern. Alternative approach: make this a sub-agent task instead of a tool — the social-media-analyst sub-agent (Task 41) already has `browse_and_research` access and can perform this analysis natively. Consider whether `analyze_social_profile` should be a tool at all, or just a prompt instruction for the social-media-analyst sub-agent. Decision should be made during implementation.

- **Acceptance Criteria**:
  - [ ] Successfully browses and extracts social profile data via `browse_and_research`
  - [ ] Provides structured brand strategy analysis
  - [ ] Works for Instagram (primary), Facebook, TikTok
  - [ ] Graceful fallback if profile is private or platform blocks access

### Component 3: get_search_autocomplete Tool

#### Requirement 1 - Google Autocomplete Suggestions
- **Requirement**: Simple REST call to get Google autocomplete suggestions
- **Implementation**:
  - `src/shared/src/shared/agent_tools/analysis/get_search_autocomplete.py`
  ```python
  import httpx

  from loguru import logger


  GOOGLE_AUTOCOMPLETE_URL = (
      "https://suggestqueries.google.com/complete/search"
  )


  def _fetch_autocomplete(
      query: str,
      language: str = "vi",
      country: str = "vn",
  ) -> list[str]:
      """
      Fetch Google autocomplete suggestions.

      Args:
          query: Partial search query
          language: Language code (vi for Vietnamese)
          country: Country code (vn for Vietnam)

      Returns:
          List of autocomplete suggestion strings
      """
      params = {
          "client": "firefox",
          "q": query,
          "hl": language,
          "gl": country,
      }
      try:
          response = httpx.get(
              GOOGLE_AUTOCOMPLETE_URL,
              params=params,
              timeout=10.0,
          )
          response.raise_for_status()
          data = response.json()
          if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
              return data[1]
          return []
      except Exception as e:
          logger.warning(f"Autocomplete request failed for '{query}': {e}")
          return []


  def get_search_autocomplete(
      query: str,
      language: str = "vi",
      variants: list[str] | None = None,
  ) -> str:
      """
      Get Google autocomplete suggestions for keyword research.

      Reveals what people are actually searching for related to
      a topic. Useful for:
      - Discovering customer language and terminology
      - Finding popular search patterns in a category
      - Understanding what questions people ask about F&B topics

      Args:
          query: Base search query (e.g., "quán café specialty")
          language: Language — "vi" (Vietnamese, default), "en" (English)
          variants: Additional query prefixes to try
              (e.g., ["how to", "best", "why"]). Each generates
              separate autocomplete results.

      Returns:
          Autocomplete suggestions grouped by query variant
      """
      all_suggestions: dict[str, list[str]] = {}

      # Step 1: Fetch for base query
      try:
          base_results = _fetch_autocomplete(query, language=language)
          all_suggestions[query] = base_results
      except Exception as e:
          logger.warning(f"Autocomplete failed for '{query}': {e}")
          all_suggestions[query] = []

      # Step 2: Fetch for each variant prefix
      if variants:
          for variant in variants:
              variant_query = f"{variant} {query}"
              try:
                  results = _fetch_autocomplete(variant_query, language=language)
                  all_suggestions[variant_query] = results
              except Exception as e:
                  logger.warning(f"Autocomplete failed for '{variant_query}': {e}")
                  all_suggestions[variant_query] = []

      # Step 3: Format output
      if not any(all_suggestions.values()):
          return f"No autocomplete suggestions found for '{query}'."

      lines = [f"## Autocomplete Suggestions for: {query}\n"]

      for variant_query, suggestions in all_suggestions.items():
          if variant_query == query:
              lines.append(f"### Base query: `{query}`")
          else:
              lines.append(f"### Variant: `{variant_query}`")

          if suggestions:
              for s in suggestions:
                  lines.append(f"- {s}")
          else:
              lines.append("- _(no suggestions)_")
          lines.append("")

      total = sum(len(s) for s in all_suggestions.values())
      lines.append(f"**Total suggestions**: {total}")
      return "\n".join(lines)
  ```
- **Implementation Logic**:
  1. Fetch autocomplete for base query
  2. If variants provided, fetch for each variant + base query
  3. Deduplicate and format results
  4. Group by variant for readability

- **Acceptance Criteria**:
  - [ ] Returns 10+ suggestions for a query
  - [ ] Vietnamese language support works
  - [ ] Variant expansion (e.g., "best + query", "how to + query")
  - [ ] No API key required (free, unofficial endpoint)

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: Review Analysis — Single Business
- **Purpose**: Verify single-business review analysis
- **Steps**:
  1. Call `analyze_reviews(business_name="The Workshop Coffee", location="District 1, HCMC")`
  2. Verify structured output with themes and quotes
- **Expected Result**: Sentiment analysis with positive/negative themes, key quotes
- **Status**: ⏳ Pending

### Test Case 2: Review Analysis — Category-Wide
- **Purpose**: Verify area-wide category review analysis
- **Steps**:
  1. Call `analyze_reviews(query="specialty coffee", location="District 3, HCMC", max_businesses=3)`
  2. Verify aggregated analysis across multiple businesses
- **Expected Result**: Cross-business themes and unmet needs
- **Status**: ⏳ Pending

### Test Case 3: Social Profile Analysis
- **Purpose**: Verify Instagram profile brand analysis
- **Steps**:
  1. Call `analyze_social_profile(platform="instagram", username="some_coffee_brand")`
  2. Verify structured brand assessment
- **Expected Result**: Content strategy, visual identity, engagement assessment
- **Status**: ⏳ Pending

### Test Case 4: Autocomplete Suggestions
- **Purpose**: Verify autocomplete retrieval
- **Steps**:
  1. Call `get_search_autocomplete("quán café specialty", variants=["best", "giá rẻ"])`
  2. Verify 10+ suggestions returned
- **Expected Result**: Suggestions in Vietnamese, grouped by variant
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation.

### What Was Implemented

**Components Completed**:
- [ ] [Component 1]: analyze_reviews Tool
- [ ] [Component 2]: analyze_social_profile Tool
- [ ] [Component 3]: get_search_autocomplete Tool

**Files Created/Modified**:
```
src/prompts/brand_strategy/
├── analyze_reviews.py             # REVIEW_ANALYSIS_PROMPT
└── analyze_social_profile.py      # SOCIAL_ANALYSIS_PROMPT

src/shared/src/shared/agent_tools/analysis/
├── __init__.py                    # Package exports
├── analyze_reviews.py             # Review sentiment analysis tool (imports prompts)
├── analyze_social_profile.py      # Social media brand analysis tool (imports prompts)
└── get_search_autocomplete.py     # Google autocomplete tool (no LLM prompt)
```

------------------------------------------------------------------------
