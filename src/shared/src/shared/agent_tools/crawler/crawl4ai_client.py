"""
Crawl4AI Client for clean web content extraction optimized for LLM consumption.
Uses official Crawl4AI SDK for better configuration and reliability.
"""

import asyncio
import traceback
from typing import List, Optional

from crawl4ai import BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.docker_client import Crawl4aiDockerClient
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from loguru import logger
from pydantic import BaseModel, Field

from shared.utils.base_class import ScrapeResult


class ContentExtractionResult(BaseModel):
    status: str = Field(
        ...,
        description=(
            "Status of the content extraction. Possible values: "
            "'no_content', 'not_cleaned', 'cleaned'."
        ),
    )
    start_sentence: str = Field(
        "", description="The starting sentence of the main content."
    )
    end_sentence: str = Field(
        "", description="The ending sentence of the main content."
    )


class Crawl4AIConfig(BaseModel):
    """Configuration for Crawl4AI web scraping optimized for LLM content."""

    # Basic crawling config
    url: str = Field(..., description="URL to crawl")

    # Content cleaning parameters for LLM optimization
    only_text: bool = Field(True, description="Extract text-only content")
    excluded_tags: List[str] = Field(
        default=[
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "aside",
            "iframe",
            "form",
        ],
        description="HTML tags to exclude for cleaner content",
    )
    excluded_selector: Optional[str] = Field(
        default="[class*='ad'], [class*='banner'], [class*='popup'], [id*='ad']",
        description="CSS selectors to exclude ads and noise",
    )
    css_selector: Optional[str] = Field(
        None, description="Focus on specific content area"
    )

    # Content filtering
    word_count_threshold: int = Field(10, description="Minimum words per text block")
    remove_forms: bool = Field(True, description="Remove form elements")

    # Image and media handling
    exclude_external_images: bool = Field(True, description="Remove external images")
    image_description_min_word_threshold: int = Field(
        5, description="Min words for image descriptions"
    )

    # Advanced cleaning
    fit_markdown: bool = Field(
        True, description="Use heuristic filtering for AI-friendly content"
    )
    prettiify: bool = Field(True, description="Clean and format HTML")

    # Performance
    cache_mode: str = Field("enabled", description="Cache mode for repeated requests")
    timeout: int = Field(30, description="Request timeout in seconds")


class Crawl4AIClient:
    """Client using official Crawl4AI Docker SDK for web scraping."""

    def __init__(
        self,
        base_url: str = "http://localhost:11235",
        timeout: float = 60.0,
        verbose: bool = True,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.verbose = verbose

    async def _get_client(self) -> Crawl4aiDockerClient:
        """Get Docker client instance."""
        return Crawl4aiDockerClient(
            base_url=self.base_url, timeout=self.timeout, verbose=self.verbose
        )

    def _run_async(self, coro):
        """Helper to run async functions in sync context."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create new event loop for nested calls
                import threading

                result = None
                exception = None

                def run_in_thread():
                    nonlocal result, exception
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        result = new_loop.run_until_complete(coro)
                        new_loop.close()
                    except Exception as e:
                        exception = e

                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join()

                if exception:
                    raise exception
                return result
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(coro)

    def fetch_clean_content(
        self, url: str, config: Optional[Crawl4AIConfig] = None
    ) -> ScrapeResult:
        """
        Extract clean, LLM-optimized content from a website.

        Args:
            url: URL to crawl
            config: Optional configuration for crawling behavior

        Returns:
            ScrapeResult with clean content
        """
        if not config:
            config = Crawl4AIConfig(
                url=url,
                only_text=True,
                css_selector=None,
                word_count_threshold=10,
                remove_forms=True,
                exclude_external_images=True,
                image_description_min_word_threshold=5,
                fit_markdown=True,
                prettiify=True,
                cache_mode="enabled",
                timeout=30,
            )
        else:
            config.url = url

        async def _crawl():
            try:
                client = await self._get_client()

                async with client:
                    # Configure browser
                    browser_config = BrowserConfig(headless=True)

                    # Configure markdown generator
                    markdown_generator = DefaultMarkdownGenerator(
                        options={
                            "ignore_images": True,
                            "ignore_links": config.only_text,
                            "body_width": 0,
                        }
                    )

                    # Configure content filter based on config
                    content_filter = None
                    if config.fit_markdown:
                        content_filter = PruningContentFilter(
                            threshold=0.45,
                            threshold_type="dynamic",
                            min_word_threshold=config.word_count_threshold,
                        )
                        # Apply content filter to markdown generator
                        markdown_generator = DefaultMarkdownGenerator(
                            content_filter=content_filter,
                            options={
                                "ignore_images": True,
                                "ignore_links": config.only_text,
                                "body_width": 0,
                            },
                        )

                    # Configure crawler
                    crawler_config = CrawlerRunConfig(
                        cache_mode=(
                            CacheMode.BYPASS
                            if config.cache_mode == "bypass"
                            else CacheMode.ENABLED
                        ),
                        excluded_tags=config.excluded_tags,
                        excluded_selector=config.excluded_selector,
                        css_selector=config.css_selector,
                        word_count_threshold=config.word_count_threshold,
                        remove_forms=config.remove_forms,
                        exclude_external_images=config.exclude_external_images,
                        markdown_generator=markdown_generator,
                    )

                    results = await client.crawl(
                        urls=[url],
                        browser_config=browser_config,
                        crawler_config=crawler_config,
                    )

                    if results:
                        result = results[0] if isinstance(results, list) else results
                        if result.success and result.markdown:
                            content = self._post_process_content(result.markdown)
                            logger.info(
                                f"Successfully crawled {url} - {len(content)} "
                                "characters"
                            )
                            return ScrapeResult(url=url, content=content)
                        else:
                            error_msg = (
                                result.error_message
                                if hasattr(result, "error_message")
                                else "Unknown error"
                            )
                            logger.error(f"Crawl failed: {error_msg}")
                            return ScrapeResult(url=url, content="")
                    else:
                        logger.error("No results returned from crawl")
                        return ScrapeResult(url=url, content="")

            except Exception as e:
                logger.error(f"Error crawling {url} with Crawl4AI Docker SDK: {e}")
                return ScrapeResult(url=url, content="")

        return self._run_async(_crawl())

    # ========== NEW MULTI-MODE METHODS ==========

    def fetch_content_summary(self, url: str) -> ScrapeResult:
        """
        Extract and summarize website content using local LLM processing.

        Args:
            url: URL to crawl

        Returns:
            ScrapeResult with structured summary
        """
        try:
            # First get basic crawl content using balanced preset
            basic_result = self.fetch_clean_content(url, Crawl4AIPresets.balanced())

            if not basic_result.content:
                logger.warning(f"No basic content available for summarization: {url}")
                return ScrapeResult(url=url, content="")

            # Use local LLM to create summary
            summary_content = self._summarize_content_with_llm(basic_result.content)

            logger.info(
                f"Summary extraction completed for {url} - {len(summary_content)} "
                f"characters"
            )
            return ScrapeResult(url=url, content=summary_content)

        except Exception as e:
            logger.error(f"Summary extraction failed for {url}: {e}")
            return ScrapeResult(url=url, content="")

    def _filter_content_with_llm(self, content: str, query: str) -> str:
        """Use Gemini AI to filter content relevant to user query."""
        try:
            from config.system_config import SETTINGS
            from prompts.extract_web_content.filter_relevant_content import (
                FILTER_RELEVANT_CONTENT_PROMPT,
            )
            from shared.model_clients.llm.google import (
                GoogleAIClientLLM,
                GoogleAIClientLLMConfig,
            )

            llm = GoogleAIClientLLM(
                config=GoogleAIClientLLMConfig(
                    model="gemini-2.5-flash-lite",
                    api_key=SETTINGS.GEMINI_API_KEY,
                    thinking_budget=0,
                    response_mime_type="text/plain",
                )
            )

            prompt = FILTER_RELEVANT_CONTENT_PROMPT.replace(
                "{{user_query}}", query
            ).replace("{{content}}", content)

            result = llm.complete(prompt, temperature=0.1).text

            logger.debug(f"LLM content filtering completed for query: {query}")
            return result.strip()

        except Exception as e:
            logger.warning(f"LLM content filtering failed: {e}, using original content")
            logger.warning(traceback.format_exc())
            return content

    def _summarize_content_with_llm(self, content: str) -> str:
        """Use Gemini AI to create structured summary of content."""
        try:
            from config.system_config import SETTINGS
            from prompts.extract_web_content.summarize_content import (
                SUMMARIZE_CONTENT_PROMPT,
            )
            from shared.model_clients.llm.google import (
                GoogleAIClientLLM,
                GoogleAIClientLLMConfig,
            )

            llm = GoogleAIClientLLM(
                config=GoogleAIClientLLMConfig(
                    model="gemini-2.5-flash-lite",
                    api_key=SETTINGS.GEMINI_API_KEY,
                    thinking_budget=0,
                    response_mime_type="text/plain",
                )
            )

            prompt = SUMMARIZE_CONTENT_PROMPT.replace("{{content}}", content)

            result = llm.complete(prompt, temperature=0.1).text

            logger.debug("LLM content summarization completed")
            return result.strip()

        except Exception as e:
            logger.warning(
                f"LLM content summarization failed: {e}, using original content"
            )
            logger.warning(traceback.format_exc())
            return content

    def _extract_main_content_with_llm(self, content: str) -> str:
        """Use Gemini AI to define main content boundaries like Tavily approach."""
        try:
            import json

            from config.system_config import SETTINGS
            from prompts.extract_web_content.find_main_content import (
                MAIN_CONTENT_SEARCH_PROMPT,
            )
            from shared.model_clients.llm.google import (
                GoogleAIClientLLM,
                GoogleAIClientLLMConfig,
            )

            llm = GoogleAIClientLLM(
                config=GoogleAIClientLLMConfig(
                    model="gemini-2.5-flash-lite",
                    api_key=SETTINGS.GEMINI_API_KEY,
                    thinking_budget=0,
                    response_mime_type="application/json",
                    response_schema=ContentExtractionResult,
                )
            )

            result = llm.complete(
                MAIN_CONTENT_SEARCH_PROMPT.replace("{{raw_content}}", content),
                temperature=0.1,
            ).text

            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()

            result = json.loads(result)

            if result["status"] == "no_content" or result["status"] == "not_cleaned":
                return content
            elif result["status"] == "cleaned":
                start_sentence = result["start_sentence"]
                end_sentence = result["end_sentence"]

                # Extract the content between the start and end sentences
                start_index = content.find(start_sentence)
                end_index = content.find(end_sentence, start_index)

                if start_index != -1 and end_index != -1:
                    # Extract the main content
                    main_content = content[start_index : end_index + len(end_sentence)]
                    return main_content.strip()
                else:
                    return (
                        content  # Fallback to original content if sentences not found
                    )

        except Exception as e:
            logger.warning(
                f"AI main content extraction failed: {e}, using original content"
            )
            logger.warning(traceback.format_exc())
            return content

        # Fallback return in case of unexpected execution path
        return content

    def _post_process_content(self, content: str) -> str:
        """Process content using AI main content detection + formatting cleanup."""
        import re

        # Apply AI processing
        content = self._extract_main_content_with_llm(content)

        # Then clean up formatting
        # Remove markdown links but keep text - [text](url) -> text
        content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)

        # Remove standalone links
        content = re.sub(r"https?://[^\s\n]+", "", content)

        # Remove image references
        content = re.sub(r"!\[.*?\]\([^)]*\)", "", content)

        # Remove excessive whitespace
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = re.sub(r"[ \t]+", " ", content)

        # Clean up and trim
        content = content.strip()

        return content

    def fetch_relevant_content(self, url: str, query: str) -> ScrapeResult:
        """
        Extract website content relevant to a specific query using local LLM filtering.

        Args:
            url: URL to crawl
            query: Query to filter relevant content

        Returns:
            ScrapeResult with LLM-filtered content
        """
        try:
            # First get basic crawl content using balanced preset
            basic_result = self.fetch_clean_content(url, Crawl4AIPresets.balanced())

            if not basic_result.content:
                logger.warning(f"No basic content available for LLM filtering: {url}")
                return ScrapeResult(url=url, content="")

            # Use local LLM to filter relevant content
            filtered_content = self._filter_content_with_llm(
                basic_result.content, query
            )

            logger.info(
                f"LLM-filtered crawl completed for {url} - {len(filtered_content)} "
                f"characters"
            )
            return ScrapeResult(url=url, content=filtered_content)

        except Exception as e:
            logger.error(f"Error in LLM-filtered crawl for {url}: {e}")
            return ScrapeResult(url=url, content="")


# Factory function for easy usage
def create_crawl4ai_client(
    base_url: str = "http://localhost:11235",
    timeout: float = 60.0,
    verbose: bool = False,
) -> Crawl4AIClient:
    """Create a Crawl4AI Docker client instance."""
    return Crawl4AIClient(base_url=base_url, timeout=timeout, verbose=verbose)


# Configuration presets for different use cases
class Crawl4AIPresets:
    """Predefined configurations for common crawling scenarios."""

    @staticmethod
    def lenient() -> Crawl4AIConfig:
        """Lenient configuration to get maximum content first."""
        return Crawl4AIConfig(
            url="",
            only_text=True,
            css_selector=None,  # No selector restrictions
            excluded_selector=None,  # No exclusions
            excluded_tags=["script", "style", "iframe"],  # Only obvious noise
            word_count_threshold=0,  # Keep all text blocks
            remove_forms=True,
            exclude_external_images=False,  # Keep captions/figures
            image_description_min_word_threshold=0,
            fit_markdown=False,  # No content filter initially
            prettiify=True,
            cache_mode="enabled",
            timeout=30,
        )

    @staticmethod
    def balanced() -> Crawl4AIConfig:
        """Balanced configuration with light filtering."""
        return Crawl4AIConfig(
            url="",
            only_text=True,
            css_selector=None,  # Let Crawl4AI auto-detect main content
            excluded_selector=(
                ".ads, .advertisement, .cookie, .newsletter, .promo, "
                "[id^='ad-'], [class^='ad-']"
            ),
            excluded_tags=["script", "style", "iframe", "form"],
            word_count_threshold=3,  # Very low threshold
            remove_forms=True,
            exclude_external_images=False,  # Keep captions
            image_description_min_word_threshold=5,
            fit_markdown=False,
            prettiify=True,
            cache_mode="enabled",
            timeout=30,
        )

    @staticmethod
    def strict() -> Crawl4AIConfig:
        """Strict configuration for heavily filtered content."""
        return Crawl4AIConfig(
            url="",
            only_text=True,
            css_selector="main, article, .content, .post, .entry-content",
            excluded_selector=(
                ".ads, .advertisement, .cookie, .newsletter, .promo, "
                "[id^='ad-'], [class^='ad-'], nav, header, footer, aside"
            ),
            excluded_tags=[
                "script",
                "style",
                "nav",
                "header",
                "footer",
                "aside",
                "iframe",
                "form",
                "button",
            ],
            word_count_threshold=5,
            remove_forms=True,
            exclude_external_images=False,  # Still keep captions
            image_description_min_word_threshold=5,
            fit_markdown=True,  # Enable content filter
            prettiify=True,
            cache_mode="enabled",
            timeout=30,
        )
