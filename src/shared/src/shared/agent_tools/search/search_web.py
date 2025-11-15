import json
import logging
import os
import random
import re
import subprocess
import threading
import time
from typing import Any, Dict, List

import requests
from loguru import logger

from shared.agent_tools.search.exceptions import LoadCrapelessDeepSerpTokenError
from shared.utils.base_class import Payload, SearchResult

logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Global throttle lock: ensures only one search request is in-flight to
# SearXNG at a time
_SEARXNG_THROTTLE_LOCK = threading.Lock()
_LAST_SEARXNG_TIME = 0.0
_MIN_SEARXNG_DELAY = 3.5


def deep_serp_search(query: str, number_of_results: int = 5) -> List[SearchResult]:
    """
    This tool uses the Scrapeless API to perform a deep search on Google SERP.

    Arguments:
        query (str): The search query to perform on Google.
        number_of_results (int): The number of search results to return. Default is 5.

    Returns:
        List[SearchResult]: List of search results from Google SERP, each
            containing title, url, and snippet.
    """
    host = "api.scrapeless.com"
    url = f"https://{host}/api/v1/scraper/request"
    token = os.getenv("SCRAPELESS_API_KEY", "")

    if not token:
        logger.error(
            LoadCrapelessDeepSerpTokenError(
                "Scrapeless API token not found. Please set the SCRAPELESS_API_TOKEN "
                "environment variable."
            )
        )
        return []

    # Set up the headers and payload for the API request
    headers = {"x-api-token": token}
    input_data = {
        "q": query,
        "gl": "vn",
        "hl": "vi",
        "location": "Ho Chi Minh City, Viet Nam",
        "google_domain": "google.com.vn",
        "num": f"{number_of_results}",
    }
    payload = Payload(actor="scraper.google.search", input=input_data)
    json_payload = json.dumps(payload.__dict__)

    # Make the API request
    response = requests.post(url, headers=headers, data=json_payload, timeout=30)

    if response.status_code != 200:
        logger.error(
            LoadCrapelessDeepSerpTokenError(
                f"Error:{response.status_code} - {response.text}"
            )
        )
        return []
    else:
        data = response.json()
        results = data.get("organic_results", [])

        # If there are no results, return an empty list
        if not results:
            logger.error(
                LoadCrapelessDeepSerpTokenError("No results found in the response.")
            )
            return []

        search_results = []
        for result in results:
            search_result = SearchResult(
                title=result.get("title", "No title"),
                url=result.get("link", ""),
                snippet=result.get("snippet", ""),
            )
            search_results.append(search_result)

        return search_results


def search_web(queries: List[str], top_k: int = 5) -> Dict[str, Any]:
    """
    Google Search tool to find relevant information on the web with sequential
    execution.
    Use this function to perform web searches for a list of queries.

    Features:
    - Query deduplication to reduce unnecessary requests
    - Rate limiting (3.5s delay between requests per engine)
    - Automatic exponential backoff on rate limit (429) responses
    - Sequential execution to prevent rate limiting
    - Automatic fallback to next engine if current fails

    Args:
        queries (List[str]): List of search queries to find relevant information.
        top_k (int): The number of top results to return per query (default: 5).

    Returns:
        dict: A dictionary with structure:
            {
                "queries": {
                    "query1": {
                        "results": List[SearchResult],
                        "response_time": float,
                        "result_count": int,
                        "engine_used": str
                    }
                },
                "total_execution_time": float,
                "total_queries": int,
                "average_time_per_query": float
            }
    """
    # Use container hostname when running in Docker, localhost when running locally
    searxng_host = os.getenv("SEARXNG_HOST", "localhost")
    searxng_port = os.getenv("SEARXNG_PORT", "8080")
    url = f"http://{searxng_host}:{searxng_port}"
    language = "vi"
    format = "json"
    engines = [
        "duckduckgo",  # Try first (CAPTCHA risk but good results when works)
        "brave",  # Fallback: works reliably
        "startpage",  # Fallback: Google-like results
        "google",  # Last resort: often returns 0 results but try anyway
    ]

    logger.info(f"Starting web search for list of following queries: {queries}")

    # Rate limiting configuration (prevent blocking from upstream engines)
    MIN_DELAY_BETWEEN_REQUESTS = 3.5  # 3.5 second delay between requests to same engine
    last_request_time: Dict[str, float] = {}  # Track last request time per engine

    # Per-engine circuit breaker state to avoid repeatedly hitting failing engines
    engine_failures: Dict[str, int] = {f"engine_{e}": 0 for e in engines}
    engine_disabled_until: Dict[str, float] = {f"engine_{e}": 0.0 for e in engines}
    FAILURE_THRESHOLD = 3  # number of consecutive failures to disable an engine
    COOL_DOWN_SECONDS = 60  # disable engine for 60s after threshold

    # Deduplicate queries to reduce unnecessary requests
    unique_queries = list(dict.fromkeys(queries))  # Preserve order while deduplicating
    if len(unique_queries) < len(queries):
        logger.info(f"Deduplicated queries: {len(queries)} → {len(unique_queries)}")
        queries = unique_queries

    def search_single_query(query: str):
        """Helper function to search a single query with rate limiting"""
        nonlocal last_request_time

        for engine in engines:
            params = {
                "q": query,
                "format": format,
                "engines": engine,
                "language": language,
            }

            try:
                # Circuit breaker: skip engine if it's temporarily disabled
                engine_key = f"engine_{engine}"
                now_ts = time.time()
                if engine_disabled_until.get(engine_key, 0) > now_ts:
                    logger.debug(
                        f"Skipping engine {engine} (disabled until "
                        f"{engine_disabled_until[engine_key]:.0f})"
                    )
                    continue

                # Rate limiting: add delay if last request was too recent
                if engine_key in last_request_time:
                    time_since_last = time.time() - last_request_time[engine_key]
                    if time_since_last < MIN_DELAY_BETWEEN_REQUESTS:
                        sleep_time = MIN_DELAY_BETWEEN_REQUESTS - time_since_last
                        logger.debug(
                            f"Rate limiting: sleeping {sleep_time:.3f}s before "
                            f"next {engine} request"
                        )
                        time.sleep(sleep_time)

                # Global throttle: ensure only one SearXNG request at a time
                global _SEARXNG_THROTTLE_LOCK, _LAST_SEARXNG_TIME, _MIN_SEARXNG_DELAY
                with _SEARXNG_THROTTLE_LOCK:
                    time_since_last_searxng = time.time() - _LAST_SEARXNG_TIME
                    if time_since_last_searxng < _MIN_SEARXNG_DELAY:
                        sleep_time = _MIN_SEARXNG_DELAY - time_since_last_searxng
                        # Add small jitter (0-0.2s) for natural behavior
                        jitter = random.uniform(0, 0.2)
                        sleep_time += jitter
                        logger.debug(
                            f"Global throttle: sleeping {sleep_time:.3f}s to maintain "
                            f"{_MIN_SEARXNG_DELAY}s interval"
                        )
                        time.sleep(sleep_time)

                    start_time = time.time()
                    rs = requests.get(url, params=params, timeout=30)
                    _LAST_SEARXNG_TIME = time.time()
                    response_time = time.time() - start_time

                last_request_time[engine_key] = time.time()

                if rs.status_code != 200:
                    # Increment failure counter for this engine
                    engine_failures[engine_key] = engine_failures.get(engine_key, 0) + 1

                    # If we exceed threshold, disable this engine temporarily
                    if engine_failures[engine_key] >= FAILURE_THRESHOLD:
                        engine_disabled_until[engine_key] = (
                            time.time() + COOL_DOWN_SECONDS
                        )
                        logger.warning(
                            f"Engine {engine} disabled for {COOL_DOWN_SECONDS}s after "
                            f"{engine_failures[engine_key]} failures"
                        )

                    # Handle rate limiting (429) and server errors (5xx)
                    # with jittered backoff
                    if rs.status_code == 429 or 500 <= rs.status_code < 600:
                        backoff = 2.0 * (1 + random.random())
                        logger.warning(
                            f"Engine {engine} returned {rs.status_code}; backing off "
                            f"{backoff:.2f}s before next engine"
                        )
                        time.sleep(backoff)

                    logger.warning(
                        (
                            f"Engine {engine} returned status {rs.status_code} "
                            f'for query "{query}", trying next engine'
                        )
                    )
                    continue

                # Success — reset failure counter
                engine_failures[engine_key] = 0

                results = rs.json().get("results", [])

                final_results: List[SearchResult] = []
                for result in results:
                    if "content" in result and result["content"]:
                        content = result["content"]
                        search_result = SearchResult(
                            title=result.get("title", "").capitalize(),
                            url=result.get("url", ""),
                            snippet=content,
                        )
                        final_results.append(search_result)

                    if len(final_results) >= top_k:
                        break

                # If we found results, return them
                if final_results:
                    logger.info(
                        f'Query "{query}" found {len(final_results)} results '
                        f"using engine: {engine}"
                    )
                    return query, final_results, response_time, engine
                else:
                    logger.warning(
                        f"Engine {engine} returned 0 useful results for query "
                        f'"{query}", trying next engine'
                    )

            except Exception as e:
                logger.error(f'Error searching for query "{query}": {str(e)}')
                return query, [], 0.0, "none"

        # If we get here, all engines failed or returned no results
        logger.warning(
            "All SearXNG engines failed or returned no results "
            f'for query "{query}", trying direct Bing search'
        )

        # Fallback: try direct Bing search using bing_web_search()
        try:
            start_time = time.time()
            bing_results = bing_web_search(query, top_k=top_k)
            response_time = time.time() - start_time

            if bing_results:
                logger.info(
                    f'Query "{query}" found {len(bing_results)} results using '
                    "fallback: bing_web_search"
                )
                return query, bing_results, response_time, "bing_direct"
            else:
                logger.warning(
                    f'Bing direct search also returned no results for query "{query}"'
                )
        except Exception as e:
            logger.error(f"Error in Bing fallback search: {str(e)}")

        return query, [], 0.0, "none"

    # Execute searches sequentially to avoid rate limiting
    results_dict = {}
    total_start_time = time.time()

    for query in queries:
        query_text, results, response_time, engine_used = search_single_query(query)
        results_dict[query_text] = {
            "results": results,
            "response_time": response_time,
            "result_count": len(results),
            "engine_used": engine_used,
        }

    total_time = time.time() - total_start_time

    response = {
        "queries": results_dict,
        "total_execution_time": total_time,
        "total_queries": len(queries),
        "average_time_per_query": total_time / len(queries) if queries else 0,
    }

    logger.info(f"Total execution time: {response['total_execution_time']:.2f} seconds")
    logger.info(
        f"Average time per query: {response['average_time_per_query']:.2f} seconds"
    )

    # Access results for each query
    log_data = []
    for query, data in response["queries"].items():  # type: ignore[attr-defined]
        log_data.append(f"\nQuery: {query}")
        log_data.append(f"Results found: {data['result_count']}")
        log_data.append(f"Engine used: {data['engine_used']}")
        log_data.append(f"Response time: {data['response_time']:.2f} seconds")
        for i, result in enumerate(data["results"][:2], 1):  # Show first 2 results
            log_data.append(f"  {i}. {result.title}")
            log_data.append(f"     URL: {result.url}")
            log_data.append(f"     Snippet: {result.snippet[:100]}...")
    logger.info("\n".join(log_data))

    return response


def bing_web_search(query: str, top_k: int = 10) -> List[SearchResult]:
    """
    Search **Bing.com** directly using curl.

    This function performs web searches on Bing and parses results
    from the HTML response.
    It's optimized for both Vietnamese and English queries with high accuracy.

    Args:
        query (str): Search query (supports Vietnamese and English)
        top_k (int): Number of results to return (default: 10)

    Returns:
        List[SearchResult]: List of search results, each containing:
            - title (str): Result title
            - url (str): Result URL
            - snippet (str): Result snippet/description

    Example:
        >>> results = bing_web_search("cách làm phở bò", top_k=5)
        >>> for result in results:
        ...     print(f"{result.title}: {result.url}")
    """
    import base64
    import html as html_lib
    import urllib.parse

    try:
        # Detect language from query: if contains Vietnamese characters
        # → Vietnamese locale, else English
        is_vietnamese = any(
            "\u0100" <= c <= "\u01af" or "\u1e00" <= c <= "\u1eff" for c in query
        )

        # Build URL with dynamic locale based on query language
        if is_vietnamese:
            # Vietnamese: use locale params for better Vietnamese results
            params = {
                "q": query,
                "mkt": "vi-VN",
                "setlang": "vi",
                "cc": "VN",
                "count": "50",  # Force traditional results layout
            }
        else:
            # English: only send query, let Bing auto-detect from Accept-Language header
            # This gives more relevant English results than forcing en-US locale
            # count=50 forces traditional results instead of Copilot suggestion page
            params = {
                "q": query,
                "count": "50",
            }

        param_str = "&".join(
            f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()
        )
        bing_url = f"https://www.bing.com/search?{param_str}"

        logger.debug(f"Bing search URL: {bing_url}")

        # Use curl with minimal headers
        curl_cmd = [
            "curl",
            "-s",
            "-L",
            "-H",
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "-H",
            "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "-H",
            "Accept-Language: en-US,en;q=0.9,vi;q=0.8",
            bing_url,
        ]

        proc_result = subprocess.run(
            curl_cmd, capture_output=True, text=True, timeout=30
        )

        if proc_result.returncode != 0:
            logger.error(f"Curl failed with return code {proc_result.returncode}")
            return []

        html_content = proc_result.stdout

        # Helper functions
        def clean_text(text: str) -> str:
            """Clean and decode HTML text"""
            text = re.sub(r"<[^>]+>", "", text)
            text = re.sub(r"\s+", " ", text).strip()
            return html_lib.unescape(text)

        results: List[SearchResult] = []

        # First, extract the b_results section to avoid matching nested elements
        results_section_match = re.search(
            r'<ol[^>]*id="b_results"[^>]*>(.*?)</ol>', html_content, re.DOTALL
        )
        if not results_section_match:
            logger.warning(f"Could not find b_results section for query: {query}")
            return []

        results_html = results_section_match.group(1)

        # Remove style and script tags to avoid matching nested tags
        results_html = re.sub(
            r"<style[^>]*>.*?</style>", "", results_html, flags=re.DOTALL
        )
        results_html = re.sub(
            r"<script[^>]*>.*?</script>", "", results_html, flags=re.DOTALL
        )

        # Extract organic results from <li class="b_algo">
        organic_pattern = r'<li[^>]*class="b_algo"[^>]*data-id[^>]*>(.*?)</li>'
        matches = re.findall(organic_pattern, results_html, re.DOTALL)

        for match in matches:
            # Title from <h2><a>
            title_match = re.search(
                r"<h2[^>]*><a[^>]*>(.*?)</a></h2>", match, re.DOTALL
            )
            if not title_match:
                continue

            title = clean_text(title_match.group(1))

            # URL from href with base64-encoded URL parameter
            url = ""
            href_match = re.search(
                r'href="([^"]*ck/a[^"]*u=a1[^"]*)"', match
            )  # First ck/a redirect URL with base64

            if href_match:
                href = href_match.group(1)
                # Extract parameter "u" from redirect URL using substring operations
                if "u=a1" in href:
                    try:
                        # Extract the u parameter value directly using substring
                        # operations
                        u_start = href.find("u=") + 2
                        u_end = href.find("&", u_start)
                        if u_end == -1:
                            u_end = len(href)
                        encoded = href[u_start:u_end]
                        # Remove prefix "a1" from base64 string
                        if encoded.startswith("a1"):
                            encoded = encoded[2:]
                        # Add padding for base64 decoding if needed
                        padding = len(encoded) % 4
                        if padding:
                            encoded += "=" * (4 - padding)
                        # Decode base64
                        decoded = base64.b64decode(encoded).decode("utf-8")
                        url = decoded
                    except Exception:
                        pass
            else:
                # Try to get any href (fallback to direct URL)
                href_match = re.search(r'href="([^"]+)"', match)
                if href_match:
                    href = href_match.group(1)
                    # If it's a direct URL, use it
                    if href.startswith("http"):
                        url = href

            # Snippet - REQUIRED for result to be included
            # Only try <p class="b_lineclamp">
            snippet_match = re.search(
                r'<p[^>]*class="[^"]*b_lineclamp[^"]*"[^>]*>(.*?)</p>', match, re.DOTALL
            )
            if not snippet_match:
                # No snippet found - skip this result
                continue

            snippet = clean_text(snippet_match.group(1))

            # Filter out very short snippets (likely metadata, not real description)
            if snippet and len(snippet) < 20:
                continue

            # All checks passed - add result
            if title and snippet:
                results.append(SearchResult(title=title, url=url, snippet=snippet))

        # Log results
        log_data = [f"\nQuery: {query}"]
        log_data.append(f"Results found: {len(results)}")
        for i, result in enumerate(results[:2], 1):  # Show first 2 results
            log_data.append(f"  {i}. {result.title}")
            log_data.append(f"     URL: {result.url}")
            log_data.append(f"     Snippet: {result.snippet[:100]}...")
        logger.info("\n".join(log_data))

        return results[:top_k]

    except subprocess.TimeoutExpired:
        logger.error(f"Curl request timed out for query: {query}")
        return []
    except Exception as e:
        logger.error(f"Error in bing_web_search: {e}")
        return []
