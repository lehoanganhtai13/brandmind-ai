import os
import json
import requests
import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
from typing import List

import logging
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

from src.config.system_config import SETTINGS
from shared.agent_tools.exceptions import LoadCrapelessDeepSerpTokenError
from shared.utils.base_class import Payload


def deep_serp_search(query: str, number_of_results: int = 5) -> str:
    """
    This tool uses the Scrapeless API to perform a deep search on Google SERP.

    Arguments:
        query (str): The search query to perform on Google.
        number_of_results (int): The number of search results to return. Default is 5.

    Returns:
        str: A JSON string containing the search results. Each search result contains title and link.
    """
    host = "api.scrapeless.com"
    url = f"https://{host}/api/v1/scraper/request"
    token = SETTINGS.SCRAPELESS_API_KEY or os.getenv("SCRAPELESS_API_KEY", "")

    if not token:
        logger.error(
            LoadCrapelessDeepSerpTokenError(
                "Scrapeless API token not found. Please set the SCRAPELESS_API_TOKEN environment variable."
            )
        )
        return f"Scrapeless API token not found. Please set the SCRAPELESS_API_TOKEN environment variable."

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
    response = requests.post(url, headers=headers, data=json_payload)

    if response.status_code != 200:
        logger.error(
            LoadCrapelessDeepSerpTokenError(
                f"Error:{response.status_code} - {response.text}"
            )
        )
        return f"Error when calling API: {response.status_code} - {response.text}"
    else:
        data = response.json()
        results = data.get("organic_results", [])

        # If there are no results, return an empty list
        if not results:
            logger.error(
                LoadCrapelessDeepSerpTokenError("No results found in the response.")
            )
            return "No results found."

        json_results = []
        for result in results:
            json_result = {
                "title": result.get("title", "No title"),
                "link": result.get("link", "#")
            }

            json_results.append(json_result)

        return json.dumps(json_results, indent=2, ensure_ascii=False)
    
def search_web(queries: List[str], top_k: int = 53):
    """
    Google Search tool to find relevant information on the web with parallel execution.

    Args:
        queries (List[str]): List of search queries to find relevant information.
        top_k (int): The number of top results to return per query.
        max_workers (int): Maximum number of concurrent workers for parallel execution.

    Returns:
        dict: A dictionary where keys are queries and values are lists of search results.
    """
    # Use container hostname when running in Docker, localhost when running locally
    searxng_host = os.getenv("SEARXNG_HOST", "localhost")
    url = f"http://{searxng_host}:8080"
    language = "vi-VN"
    format = "json"
    engines = [
        "google",
        "duckduckgo",
        "brave",
        "startpage",
        "Swisscows",
    ]
    excluded_domains = [
        "bachhoaxanh.com",
        "dienmayxanh.com",
        "facebook.com",
        "youtube.com",
        "tiki.vn",
        "lazada.vn",
        "shopee.vn",
    ]

    logger.info(f"Starting web search for list of following queries: {queries}")

    def search_single_query(query: str):
        """Helper function to search a single query"""
        for engine in engines:
            params = {
                "q": query,
                "format": format,
                "engines": engine,
                "language": language,
            }
            
            try:
                start_time = time.time()
                rs = requests.get(url, params=params, timeout=30)
                response_time = time.time() - start_time
                
                if rs.status_code != 200:
                    logger.warning((
                        f"Engine {engine} returned status {rs.status_code} "
                        f"for query '{query}', trying next engine"
                    ))
                    continue

                results = rs.json().get("results", [])
                
                final_results = []
                for result in results:
                    if (
                        "content" in result
                        and result["content"]
                        and not any(domain in result.get("url", "") for domain in excluded_domains)
                    ):
                        content = result["content"]
                        final_results.append({
                            "title": result.get("title", "").capitalize(),
                            "url": result.get("url", ""),
                            "snippet": content,
                            "score": result.get("score", 0.0)
                        })
                    
                    if len(final_results) >= top_k:
                        break
                
                # If we found results, return them
                if final_results:
                    logger.info(f"Query '{query}' found {len(final_results)} results using engine: {engine}")
                    return query, final_results, response_time, engine
                else:
                    logger.warning(f"Engine {engine} returned 0 useful results for query '{query}', trying next engine")
                
            except Exception as e:
                logger.error(f"Error searching for query '{query}': {str(e)}")
                return query, [], 0.0, "none"

        # If we get here, all engines failed or returned no results
        logger.warning(f"All engines failed or returned no results for query '{query}'")
        return query, [], 0.0, "none"

    # Execute searches in parallel
    results_dict = {}
    total_start_time = time.time()

    max_workers = min(len(queries), 2)  # Limit to 2 workers or number of queries, whichever is smaller
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all queries
        future_to_query = {executor.submit(search_single_query, query): query for query in queries}
        
        # Collect results as they complete
        for future in as_completed(future_to_query):
            query, results, response_time, engine_used = future.result()
            results_dict[query] = {
                "results": results,
                "response_time": response_time,
                "result_count": len(results),
                "engine_used": engine_used
            }
    
    total_time = time.time() - total_start_time

    response = {
        "queries": results_dict,
        "total_execution_time": total_time,
        "total_queries": len(queries),
        "average_time_per_query": total_time / len(queries) if queries else 0
    }

    logger.info(f"Total execution time: {response['total_execution_time']:.2f} seconds")
    logger.info(f"Average time per query: {response['average_time_per_query']:.2f} seconds")

    # Access results for each query
    log_data = []
    for query, data in response["queries"].items():
        log_data.append(f"\nQuery: {query}")
        log_data.append(f"Results found: {data['result_count']}")
        log_data.append(f"Engine used: {data['engine_used']}")
        log_data.append(f"Response time: {data['response_time']:.2f} seconds")
        for i, result in enumerate(data["results"][:2], 1):  # Show first 2 results
            log_data.append(f"  {i}. {result['title']}")
            log_data.append(f"     URL: {result['url']}")
            log_data.append(f"     Snippet: {result['snippet'][:100]}...")
    logger.info("\n".join(log_data))

    return response
