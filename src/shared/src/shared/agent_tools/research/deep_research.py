"""deep_research tool — multi-step research pipeline.

Orchestrates a 4-step pipeline: (1) LLM generates targeted search
queries, (2) search_web batch search, (3) scrape_web_content crawl
top pages with relevance filtering, (4) LLM synthesize into
structured research summary with citations.

No external API dependency beyond Gemini (already required system-wide).
Uses existing search_web + scrape_web_content tools.
"""

from __future__ import annotations

import json
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from urllib.parse import urlparse

from loguru import logger

from config.system_config import SETTINGS
from prompts.research.generate_queries import GENERATE_QUERIES_PROMPT
from prompts.research.synthesize_research import SYNTHESIZE_RESEARCH_PROMPT
from shared.agent_tools.crawler.crawl_web import scrape_web_content
from shared.agent_tools.search.search_web import search_web
from shared.model_clients.llm.google import (
    GoogleAIClientLLM,
    GoogleAIClientLLMConfig,
)

# =========================================================================
# Depth Configuration
# =========================================================================

DEPTH_CONFIG: dict[str, dict[str, int]] = {
    "quick": {
        "num_queries": 2,
        "crawl_top_n": 2,
        "max_chars_per_page": 4000,
    },
    "standard": {
        "num_queries": 4,
        "crawl_top_n": 4,
        "max_chars_per_page": 6000,
    },
    "comprehensive": {
        "num_queries": 5,  # MAX: search_web enforces MAX_QUERIES=5
        "crawl_top_n": 6,
        "max_chars_per_page": 8000,
    },
}

MAX_CRAWL_WORKERS = 3


# =========================================================================
# Main Function
# =========================================================================


def deep_research(
    topic: str,
    context: str | None = None,
    depth: str = "standard",
) -> str:
    """Conduct deep research on a topic by searching the web,
    crawling top results, and synthesizing findings.

    This function orchestrates a 4-step pipeline:
        1. LLM generates targeted search queries from the topic
        2. search_web executes queries across multiple providers
        3. scrape_web_content crawls top URLs with relevance filtering
        4. LLM synthesizes all content into structured research

    Use for complex research questions that require synthesis from
    multiple sources — market trends, industry analysis, consumer
    behavior, competitive landscape.

    For simple factual queries, use search_web instead.

    Args:
        topic: Research question or topic
            (e.g., "F&B market trends Vietnam 2026").
        context: Additional context to guide research
            (e.g., "Focus on specialty coffee segment in HCMC").
        depth: Research depth level:
            - "quick": 2 queries, 2 pages (fast overview)
            - "standard": 4 queries, 4 pages (balanced, default)
            - "comprehensive": 5 queries, 6 pages (thorough)

    Returns:
        Structured markdown research summary with key findings,
        detailed analysis, implications, and source citations.
        Returns error message string if pipeline fails entirely.
    """
    logger.info(f"Starting deep research: topic='{topic}', depth='{depth}'")

    config = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["standard"])

    try:
        # Step 1: Generate targeted search queries
        queries = _generate_search_queries(
            topic=topic,
            context=context,
            num_queries=config["num_queries"],
        )
        logger.info(f"Generated {len(queries)} search queries")

        # Step 2: Execute web search
        search_results = search_web(
            queries=queries,
            number_of_results=10,
        )
        logger.info("Web search completed")

        # Step 3: Crawl top pages with relevance filtering
        ranked_urls = _rank_and_deduplicate_urls(
            search_results=search_results,
            topic=topic,
            top_n=config["crawl_top_n"],
        )
        crawled_pages = _crawl_pages_concurrent(
            urls=ranked_urls,
            topic=topic,
            max_chars=config["max_chars_per_page"],
        )
        logger.info(
            f"Crawled {len(crawled_pages)} pages (of {len(ranked_urls)} attempted)"
        )

        if not crawled_pages:
            logger.warning(
                "No pages crawled successfully, synthesizing from search snippets only"
            )

        # Step 4: Synthesize into research summary
        result = _synthesize_research(
            topic=topic,
            context=context,
            search_results=search_results,
            crawled_pages=crawled_pages,
        )
        logger.info(f"Deep research completed: {len(result)} characters")
        return result

    except Exception as e:
        logger.error(f"Deep research failed: {e}")
        logger.error(traceback.format_exc())
        return (
            f"Deep research failed for topic '{topic}': {e}. "
            f"Try using search_web for a simpler search."
        )


# =========================================================================
# Step 1: Query Generation
# =========================================================================


def _generate_search_queries(
    topic: str,
    context: str | None,
    num_queries: int,
) -> list[str]:
    """Use LLM to generate diverse search queries from the topic.

    Falls back to the original topic as a single query if LLM
    call or JSON parsing fails.

    Args:
        topic: Research topic.
        context: Additional context.
        num_queries: Number of queries to generate.

    Returns:
        List of search query strings.
    """
    try:
        llm = GoogleAIClientLLM(
            config=GoogleAIClientLLMConfig(
                model="gemini-3-flash-preview",
                api_key=SETTINGS.GEMINI_API_KEY,
                thinking_level="medium",
                response_mime_type="application/json",
            )
        )

        prompt = (
            GENERATE_QUERIES_PROMPT.replace("{{topic}}", topic)
            .replace("{{context}}", context or "No additional context")
            .replace("{{num_queries}}", str(num_queries))
        )

        result = llm.complete(prompt, temperature=0.3).text
        queries = json.loads(result.strip())

        if (
            isinstance(queries, list)
            and queries
            and all(isinstance(q, str) for q in queries)
        ):
            return queries[:num_queries]

        logger.warning(
            f"LLM returned invalid format: {type(queries)}, "
            f"falling back to topic as query"
        )
        return [topic]

    except Exception as e:
        logger.warning(f"Query generation failed: {e}, using topic as query")
        return [topic]


# =========================================================================
# Step 2 Helper: URL Ranking & Deduplication
# =========================================================================


def _rank_and_deduplicate_urls(
    search_results: dict[str, Any],
    topic: str,
    top_n: int,
) -> list[dict[str, str]]:
    """Extract, deduplicate, and rank URLs from search results.

    Deduplicates by domain (keeps first occurrence) and ranks by
    a simple relevance heuristic: snippet keyword match count.

    Args:
        search_results: Raw output from search_web().
        topic: Research topic for relevance scoring.
        top_n: Maximum number of URLs to return.

    Returns:
        List of dicts with "url", "title", "snippet" keys,
        ranked by relevance.
    """
    seen_domains: set[str] = set()
    candidates: list[dict[str, Any]] = []
    topic_words = {w for w in topic.lower().split() if len(w) > 3}

    queries_data = search_results.get("queries", {})
    for _query_key, query_data in queries_data.items():
        results = query_data.get("results", [])
        for r in results:
            url = r.url if hasattr(r, "url") else r.get("url", "")
            title = r.title if hasattr(r, "title") else r.get("title", "")
            snippet = r.snippet if hasattr(r, "snippet") else r.get("snippet", "")

            if not url:
                continue

            domain = urlparse(url).netloc
            if domain in seen_domains:
                continue
            seen_domains.add(domain)

            snippet_lower = snippet.lower()
            score = sum(1 for w in topic_words if w in snippet_lower)

            candidates.append(
                {
                    "url": url,
                    "title": title,
                    "snippet": snippet,
                    "score": score,
                }
            )

    candidates.sort(key=lambda x: x["score"], reverse=True)

    return [
        {"url": c["url"], "title": c["title"], "snippet": c["snippet"]}
        for c in candidates[:top_n]
    ]


# =========================================================================
# Step 3: Concurrent Crawling
# =========================================================================


def _crawl_pages_concurrent(
    urls: list[dict[str, str]],
    topic: str,
    max_chars: int,
) -> list[dict[str, str]]:
    """Crawl multiple URLs concurrently using scrape_web_content
    with relevant mode for query-filtered content extraction.

    Args:
        urls: List of URL dicts with "url", "title", "snippet".
        topic: Research topic (used as query for relevant filtering).
        max_chars: Maximum characters per page (safety truncation).

    Returns:
        List of dicts with "url", "title", "content" for
        successfully crawled pages.
    """
    if not urls:
        return []

    crawled: list[dict[str, str]] = []

    def _crawl_single(
        url_info: dict[str, str],
    ) -> dict[str, str] | None:
        try:
            result = scrape_web_content(
                web_url=url_info["url"],
                mode="relevant",
                query=topic,
            )
            content = result.content.strip()
            if not content:
                return None

            if len(content) > max_chars:
                content = content[:max_chars] + "\n\n[Content truncated]"

            return {
                "url": url_info["url"],
                "title": url_info["title"],
                "content": content,
            }
        except Exception as e:
            logger.warning(f"Failed to crawl {url_info['url']}: {e}")
            return None

    with ThreadPoolExecutor(max_workers=MAX_CRAWL_WORKERS) as executor:
        futures = [executor.submit(_crawl_single, url_info) for url_info in urls]
        for future in futures:
            result = future.result()
            if result is not None:
                crawled.append(result)

    return crawled


# =========================================================================
# Step 4: Research Synthesis
# =========================================================================


def _synthesize_research(
    topic: str,
    context: str | None,
    search_results: dict[str, Any],
    crawled_pages: list[dict[str, str]],
) -> str:
    """Synthesize search results and crawled content into a structured
    research summary using LLM.

    Args:
        topic: Research topic.
        context: Additional context.
        search_results: Raw output from search_web().
        crawled_pages: List of crawled page dicts with
            "url", "title", "content".

    Returns:
        Structured markdown research summary with citations.
    """
    snippets_text = _format_search_snippets(search_results)
    crawled_text = _format_crawled_content(crawled_pages)

    llm = GoogleAIClientLLM(
        config=GoogleAIClientLLMConfig(
            model="gemini-2.5-flash-lite",
            api_key=SETTINGS.GEMINI_API_KEY,
            thinking_budget=2000,
            response_mime_type="text/plain",
        )
    )

    prompt = (
        SYNTHESIZE_RESEARCH_PROMPT.replace("{{topic}}", topic)
        .replace("{{context}}", context or "No additional context")
        .replace("{{search_snippets}}", snippets_text)
        .replace("{{crawled_content}}", crawled_text)
    )

    result = llm.complete(prompt, temperature=0.2).text
    return result.strip()


def _format_search_snippets(
    search_results: dict[str, Any],
) -> str:
    """Format search results into readable text for synthesis prompt.

    Args:
        search_results: Raw output from search_web().

    Returns:
        Formatted markdown text with search snippets.
    """
    lines: list[str] = []
    queries_data = search_results.get("queries", {})
    for query_key, query_data in queries_data.items():
        lines.append(f"### Query: {query_key}")
        results = query_data.get("results", [])
        for r in results:
            title = r.title if hasattr(r, "title") else r.get("title", "")
            url = r.url if hasattr(r, "url") else r.get("url", "")
            snippet = r.snippet if hasattr(r, "snippet") else r.get("snippet", "")
            lines.append(f"- [{title}]({url}): {snippet}")
        lines.append("")
    return "\n".join(lines)


def _format_crawled_content(
    crawled_pages: list[dict[str, str]],
) -> str:
    """Format crawled pages into labeled sections for synthesis prompt.

    Args:
        crawled_pages: List of crawled page dicts.

    Returns:
        Formatted text with labeled source sections.
    """
    if not crawled_pages:
        return "(No pages were crawled successfully)"
    sections: list[str] = []
    for i, page in enumerate(crawled_pages, 1):
        sections.append(
            f"--- Source [{i}]: {page['title']} ---\n"
            f"URL: {page['url']}\n\n"
            f"{page['content']}\n"
        )
    return "\n".join(sections)
