import traceback
from typing import Literal, Optional
from loguru import logger

from shared.utils.base_class import ScrapeResult
from shared.agent_tools.crawler.crawl4ai_client import create_crawl4ai_client, Crawl4AIPresets


def scrape_web_content(
    web_url: str,
    mode: Literal["clean", "summary", "relevant"] = "clean",
    query: Optional[str] = None
) -> ScrapeResult:
    """
    Unified web content scraping function with multiple extraction modes.

    Args:
        web_url (str): The URL to scrape
        mode (str): Extraction mode - "clean", "summary", or "relevant"
        query (str, optional): Query for relevant content filtering (required for "relevant" mode)

    Returns:
        ScrapeResult: The result containing the URL and processed content
    """
    logger.info(f"Scraping web content from: {web_url} (mode: {mode})")

    try:
        # Create Crawl4AI client
        client = create_crawl4ai_client()

        # Execute based on mode
        if mode == "clean":
            # Mode 1: Clean content extraction
            result = client.fetch_clean_content(
                url=web_url,
                config=Crawl4AIPresets.balanced()
            )

        elif mode == "summary":
            # Mode 2: Content summarization
            result = client.fetch_content_summary(web_url)

        elif mode == "relevant":
            # Mode 3: Query-relevant content filtering
            if not query:
                logger.error("Query is required for 'relevant' mode")
                return ScrapeResult(url=web_url, content="")

            result = client.fetch_relevant_content(
                url=web_url, query=query
            )

        else:
            logger.error(f"Invalid mode: {mode}. Supported modes: clean, summary, relevant")
            return ScrapeResult(url=web_url, content="")

        # No additional legacy cleaning needed - Crawl4AI handles it

        logger.info(f"Successfully scraped {web_url} with mode '{mode}' - {len(result.content)} characters")
        return result

    except Exception as e:
        logger.error(f"Error scraping web content from {web_url} with mode '{mode}': {e}")
        logger.error(traceback.format_exc())
        return ScrapeResult(url=web_url, content="")