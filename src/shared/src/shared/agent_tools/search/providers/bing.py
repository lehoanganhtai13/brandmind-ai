"""
Bing direct search provider implementation.

This provider performs direct web scraping on Bing.com using curl,
parsing HTML results without requiring an API key. It's optimized for
both Vietnamese and English queries.
"""

import base64
import html as html_lib
import re
import subprocess
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from loguru import logger

from shared.agent_tools.search.exceptions import (
    SearchConnectionError,
    SearchResponseError,
    SearchTimeoutError,
)
from shared.agent_tools.search.models import ProviderResult
from shared.agent_tools.search.providers.base import BaseProvider
from shared.utils.base_class import SearchResult

# Curl header constants (kept short to satisfy line length limits)
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
_ACCEPT_HEADER = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
_ACCEPT_LANG = "en-US,en;q=0.9,vi;q=0.8"


class BingProvider(BaseProvider):
    """
    Search provider using direct Bing.com scraping via curl.

    This provider performs web scraping on Bing's search results page,
    extracting organic results from the HTML response. No API key is required.
    It automatically detects query language (Vietnamese or English) and
    adjusts locale parameters accordingly.

    Attributes:
        name: Provider identifier used for logging and tracking.
        engines: Single engine provider - no rotation needed.

    Note:
        This provider relies on Bing's HTML structure which may change.
        If results stop working, the parsing logic may need updates.
    """

    name: str = "bing_direct"
    engines: List[Optional[str]] = [None]

    def search(
        self,
        queries: List[str],
        engine: Optional[str],
        num_results: int,
    ) -> ProviderResult:
        """
        Execute search for multiple queries using direct Bing scraping.

        Processes queries concurrently using ThreadPoolExecutor.

        Args:
            queries: List of search query strings to process.
            engine: Ignored for this single-engine provider.
            num_results: Maximum number of results per query.

        Returns:
            ProviderResult with successful results and any failed queries.
        """
        start_time = time.time()
        success_results = {}
        failed_queries = []

        # Process queries concurrently
        with ThreadPoolExecutor(max_workers=len(queries)) as executor:
            future_to_query = {
                executor.submit(self._search_single, query, num_results): query
                for query in queries
            }

            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    results = future.result()
                    if results:
                        success_results[query] = results
                    else:
                        failed_queries.append(query)
                except Exception as e:
                    logger.error(f"Bing search error for '{query}': {e}")
                    failed_queries.append(query)

        return ProviderResult(
            success_results=success_results,
            failed_queries=failed_queries,
            engine_used=f"{self.name}_default",
            response_time=time.time() - start_time,
        )

    def _search_single(
        self,
        query: str,
        num_results: int,
    ) -> List[SearchResult]:
        """
        Execute a single search query against Bing using curl.

        Args:
            query: The search query string.
            num_results: Maximum number of results to return.

        Returns:
            List of SearchResult objects, empty list if search fails.
        """
        try:
            # Detect language from query: Vietnamese characters check
            is_vietnamese = any(
                "\u0100" <= c <= "\u01af" or "\u1e00" <= c <= "\u1eff" for c in query
            )

            # Build URL with dynamic locale based on query language
            if is_vietnamese:
                params = {
                    "q": query,
                    "mkt": "vi-VN",
                    "setlang": "vi",
                    "cc": "VN",
                    "count": "50",
                }
            else:
                params = {
                    "q": query,
                    "count": "50",
                }

            param_str = "&".join(
                f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()
            )
            bing_url = f"https://www.bing.com/search?{param_str}"

            # Build curl command with predefined headers
            curl_cmd = [
                "curl",
                "-s",
                "-L",
                "-H",
                f"User-Agent: {_USER_AGENT}",
                "-H",
                f"Accept: {_ACCEPT_HEADER}",
                "-H",
                f"Accept-Language: {_ACCEPT_LANG}",
                bing_url,
            ]

            proc_result = subprocess.run(
                curl_cmd, capture_output=True, text=True, timeout=30
            )

            if proc_result.returncode != 0:
                logger.error(
                    SearchConnectionError(
                        provider="Bing",
                        error=f"Curl failed with return code {proc_result.returncode}",
                    )
                )
                return []

            html_content = proc_result.stdout

            # Parse HTML and extract results
            results = self._parse_bing_html(html_content, query)

            return results[:num_results]

        except subprocess.TimeoutExpired:
            logger.error(SearchTimeoutError(provider="Bing", query=query))
            return []
        except Exception as e:
            logger.error(SearchResponseError(provider="Bing", error=str(e)))
            return []

    def _parse_bing_html(
        self,
        html_content: str,
        query: str,
    ) -> List[SearchResult]:
        """
        Parse Bing HTML response and extract search results.

        Args:
            html_content: Raw HTML content from Bing search page.
            query: Original query for logging purposes.

        Returns:
            List of SearchResult objects extracted from HTML.
        """
        # Extract the b_results section
        results_section_match = re.search(
            r'<ol[^>]*id="b_results"[^>]*>(.*?)</ol>', html_content, re.DOTALL
        )
        if not results_section_match:
            logger.warning(f"Could not find b_results section for query: {query}")
            return []

        results_html = results_section_match.group(1)

        # Remove style and script tags
        results_html = re.sub(
            r"<style[^>]*>.*?</style>", "", results_html, flags=re.DOTALL
        )
        results_html = re.sub(
            r"<script[^>]*>.*?</script>", "", results_html, flags=re.DOTALL
        )

        # Extract organic results from <li class="b_algo">
        organic_pattern = r'<li[^>]*class="b_algo"[^>]*data-id[^>]*>(.*?)</li>'
        matches = re.findall(organic_pattern, results_html, re.DOTALL)

        results: List[SearchResult] = []

        for match in matches:
            # Extract title
            title_match = re.search(
                r"<h2[^>]*><a[^>]*>(.*?)</a></h2>", match, re.DOTALL
            )
            if not title_match:
                continue
            title = self._clean_text(title_match.group(1))

            # Extract URL
            url = self._extract_url(match)

            # Extract snippet - required for result to be included
            snippet_match = re.search(
                r'<p[^>]*class="[^"]*b_lineclamp[^"]*"[^>]*>(.*?)</p>', match, re.DOTALL
            )
            if not snippet_match:
                continue

            snippet = self._clean_text(snippet_match.group(1))

            # Filter out very short snippets
            if snippet and len(snippet) < 20:
                continue

            if title and snippet:
                results.append(SearchResult(title=title, url=url, snippet=snippet))

        return results

    def _extract_url(self, match: str) -> str:
        """
        Extract URL from Bing result HTML, handling base64-encoded redirects.

        Args:
            match: HTML content of a single search result.

        Returns:
            Extracted URL string, empty if extraction fails.
        """
        url = ""
        href_match = re.search(r'href="([^"]*ck/a[^"]*u=a1[^"]*)"', match)

        if href_match:
            href = href_match.group(1)
            if "u=a1" in href:
                try:
                    u_start = href.find("u=") + 2
                    u_end = href.find("&", u_start)
                    if u_end == -1:
                        u_end = len(href)
                    encoded = href[u_start:u_end]

                    if encoded.startswith("a1"):
                        encoded = encoded[2:]

                    # Add padding for base64 decoding
                    padding = len(encoded) % 4
                    if padding:
                        encoded += "=" * (4 - padding)

                    decoded = base64.b64decode(encoded).decode("utf-8")
                    url = decoded
                except Exception:
                    pass
        else:
            # Fallback to direct URL
            href_match = re.search(r'href="([^"]+)"', match)
            if href_match:
                href = href_match.group(1)
                if href.startswith("http"):
                    url = href

        return url

    def _clean_text(self, text: str) -> str:
        """
        Clean and decode HTML text.

        Args:
            text: Raw HTML text to clean.

        Returns:
            Cleaned text with HTML tags removed and entities decoded.
        """
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return html_lib.unescape(text)
