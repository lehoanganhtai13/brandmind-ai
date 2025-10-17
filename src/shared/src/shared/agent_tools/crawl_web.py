import json
import os
import re
import requests

from loguru import logger
from pydantic import BaseModel, Field

from src.config.system_config import SETTINGS
from src.prompts.extract_web_content.find_main_content import MAIN_CONTENT_SEARCH_PROMPT
from shared.model_clients.llm.google import GoogleAIClientLLM, GoogleAIClientLLMConfig


class ContentExtractionResult(BaseModel):
    status: str = Field(..., description="Status of the content extraction. Possible values: 'no_content', 'not_cleaned', 'cleaned'.")
    start_sentence: str = Field("", description="The starting sentence of the main content.")
    end_sentence: str = Field("", description="The ending sentence of the main content.")


def _has_content_after_header(lines: list[str], header_index: int, max_look_ahead: int = 3) -> bool:
    """
    Check if a header has substantial content following it within a reasonable distance.
    
    Args:
        lines (list[str]): List of text lines
        header_index (int): Index of the header line
        max_look_ahead (int): Maximum number of lines to look ahead
        
    Returns:
        bool: True if substantial content follows the header
    """
    for i in range(header_index + 1, min(header_index + 1 + max_look_ahead, len(lines))):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # If we hit another header, no substantial content for this header
        if line.startswith('#'):
            return False
            
        # If we find substantial content (longer than 20 chars), return True
        if len(line) > 20:
            return True
    
    return False

def _find_header_section_start(lines: list[str], start_index: int) -> int:
    """
    Find the start of a section that consists primarily of headers.
    
    Args:
        lines (list[str]): List of text lines
        start_index (int): Index to start searching from
        
    Returns:
        int: Index where header-only section starts, or None if no such section exists
    """
    if start_index >= len(lines):
        return None
    
    consecutive_headers = 0
    total_lines_checked = 0
    section_start = None
    
    for i in range(start_index, len(lines)):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            continue
            
        total_lines_checked += 1
        
        if line.startswith('#'):
            if consecutive_headers == 0:
                section_start = i  # Mark potential start of header section
            consecutive_headers += 1
        else:
            # Reset if we encounter non-header content
            if len(line) > 20:  # Substantial content
                consecutive_headers = 0
                section_start = None
            # Short non-header lines don't reset the count (could be category labels)
    
    # Consider it a header-only section if we have at least 3 consecutive headers
    # and they make up more than 60% of the remaining content
    if (consecutive_headers >= 3 and 
        total_lines_checked > 0 and 
        consecutive_headers / total_lines_checked > 0.6):
        return section_start
    
    return None

def _remove_trailing_header_sections(lines: list[str]) -> list[str]:
    """
    Remove trailing sections that consist primarily of headers without substantial content.
    
    This function detects patterns where multiple consecutive lines are headers (starting with #)
    and removes such sections from the end of the content.
    
    Args:
        lines (list[str]): List of cleaned text lines
        
    Returns:
        list[str]: Lines with trailing header-only sections removed
    """
    if not lines:
        return lines
    
    # Find the last substantial content (non-header line with reasonable length)
    last_content_index = -1
    
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Check if this line is a header
        is_header = line.startswith('#')
        
        # Check if this line is substantial content
        # (non-header with reasonable length, or header with substantial content after it)
        is_substantial = (
            not is_header and len(line) > 20  # Non-header with decent length
            or (is_header and _has_content_after_header(lines, i))  # Header with content following
        )
        
        if is_substantial:
            last_content_index = i
            break
    
    # If we found substantial content, check if there's a header-only section after it
    if last_content_index >= 0:
        # Look for the start of header-only section
        header_section_start = _find_header_section_start(lines, last_content_index + 1)
        
        if header_section_start is not None:
            # Remove the header-only section
            return lines[:header_section_start]
    
    return lines

def clean_markdown(markdown_text: str) -> str:
    """
    Clean Markdown text according to specified rules.
    
    This function processes markdown text by:
    1. Removing lines containing markdown link structures [text](url)
    2. Removing nested images within links
    3. Removing standard markdown images
    4. Converting remaining links to plain text
    5. Removing italic formatting
    6. Adding proper spacing before numbered lists and headers
    7. Cleaning up excessive blank lines
    8. Removing redundant and empty lines
    9. Detecting and removing trailing header-only sections
    10. Normalizing whitespace and formatting
    
    Args:
        markdown_text (str): Input Markdown text to be cleaned
        
    Returns:
        str: Cleaned text with formatting and unwanted elements removed
    """
    cleaned_text = markdown_text

    # Rule 1: Remove all lines containing Markdown link structure [text](url)
    cleaned_text = re.sub(r"^.*\[.*?\]\(.*?\).*$", "", cleaned_text, flags=re.MULTILINE)

    # Rule 2: Remove images nested within links
    cleaned_text = re.sub(r"\[!\[.*?\]\(.*?\)\]\(.*?\)", "", cleaned_text)

    # Rule 3: Remove images using standard Markdown syntax
    cleaned_text = re.sub(r"!\[.*?\]\(.*?\)", "", cleaned_text)

    # Rule 4: Convert remaining links to plain text
    cleaned_text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", cleaned_text)

    # Rule 5: Remove italic formatting _text_ -> text
    cleaned_text = re.sub(r"\_(.*?)\_", r"\1", cleaned_text)

    # Rule 6: Add proper spacing before numbered lists
    cleaned_text = re.sub(r"\n+(\d+\.)", r"\n\n\1", cleaned_text)

    # Rule 7: Clean up excessive blank lines
    cleaned_text = re.sub(r"\n{3,}", "\n", cleaned_text)

    # Rule 8: Remove redundant lines and empty lines
    lines = cleaned_text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line and stripped_line != "*":
            cleaned_lines.append(stripped_line)

    # Rule 9: Detect and remove trailing header-only sections
    cleaned_lines = _remove_trailing_header_sections(cleaned_lines)

    # Rule 10: Join cleaned lines and normalize whitespace
    cleaned_text = "\n".join(cleaned_lines)

    # Rule 11: Add spacing before headers
    final_text = re.sub(r"(#+\s*)(.*?)", r"\n\1\2", cleaned_text)

    return final_text.strip()

def define_main_content(parsed_markdown: str) -> str:
    """
    Define the main content of the parsed markdown text using an LLM.
    This function uses a language model to identify and extract the main content
    from the provided markdown text. It checks if the content is already cleaned
    and structured, and if not, it attempts to extract the main content based on
    the start and end sentences defined by the model.
    
    Args:
        parsed_markdown (str): The parsed markdown text
        
    Returns:
        str: The main content extracted from the markdown
    """

    llm = GoogleAIClientLLM(
        config=GoogleAIClientLLMConfig(
            model="gemini-2.5-flash",
            api_key=SETTINGS.GEMINI_API_KEY,
            thinking_budget=0,
            response_mime_type="application/json",
            response_schema=ContentExtractionResult,
        )
    )

    result = llm.complete(
        MAIN_CONTENT_SEARCH_PROMPT.replace("{{raw_content}}", parsed_markdown),
        temperature=0.1
    ).text

    if result.startswith("```json"):
        result = result.replace("```json", "").replace("```", "").strip()

    result = json.loads(result)

    if result["status"] == "no_content" or result["status"] == "not_cleaned":
        return parsed_markdown
    elif result["status"] == "cleaned":
        start_sentence = result["start_sentence"]
        end_sentence = result["end_sentence"]

        # Extract the content between the start and end sentences
        start_index = parsed_markdown.find(start_sentence)
        end_index = parsed_markdown.find(end_sentence, start_index)

        if start_index != -1 and end_index != -1:
            # Extract the main content
            main_content = parsed_markdown[start_index:end_index + len(end_sentence)]
            return main_content.strip()
        else:
            return parsed_markdown  # Fallback to original content if sentences not found

def scrape_web_content(web_url: str) -> dict:
    """
    Scrape web content from a given URL and return structured data.
    
    Args:
        web_url (str): The URL to scrape
        
    Returns:
        dict: A dictionary containing the scraped results
    """
    api_key = SETTINGS.TAVILY_API_KEY or os.getenv("TAVILY_API_KEY", "")

    logger.info(f"Scraping web content from: {web_url}")

    # Make a request to the Tavily API to extract content from the provided URL
    tavily_url = "https://api.tavily.com/extract"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {"urls": [web_url]}
    response = requests.post(tavily_url, json=payload, headers=headers)

    if response.status_code != 200:
        logger.error(f"Failed to fetch content from {web_url}. Status code: {response.status_code}")
        raise Exception(f"Failed to fetch content from {web_url}. Status code: {response.status_code}")

    raw_content = response.json()["results"][0]["raw_content"]
    
    # Clean the raw markdown content using the defined cleaning function
    cleaned_content = clean_markdown(raw_content)

    # Double-check to ensure the main content is defined
    cleaned_content = define_main_content(cleaned_content)

    return {
        "url": web_url,
        "content": cleaned_content,
    }
