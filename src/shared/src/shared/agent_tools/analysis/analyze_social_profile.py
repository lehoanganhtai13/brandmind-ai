"""analyze_social_profile tool — Social media brand strategy analysis.

Uses browser automation to visit a profile and Gemini LLM to analyze
the brand strategy communicated through social media presence.
"""

from __future__ import annotations

import asyncio
import threading

from loguru import logger

from config.system_config import SETTINGS
from prompts.brand_strategy.analyze_social_profile import SOCIAL_ANALYSIS_PROMPT
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
    """Analyze a social media profile's brand strategy.

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
        Structured brand strategy analysis of the social profile.
    """
    # Step 1: Build profile URL and infer platform
    if not profile_url and not username:
        return "Either profile_url or username must be provided."

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
            return (
                f"Unsupported platform: {platform}. Use instagram, facebook, or tiktok."
            )
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

    # Step 3: Call browse_and_research (async → sync bridge)
    try:
        manager = BrowserManager()
        browse_fn = create_browse_tool(manager)
        coro = browse_fn(browse_task)

        # Thread-based sync→async bridge (handles nested event loops)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                result_holder: list[str | None] = [None]
                exc_holder: list[BaseException | None] = [None]

                def _run() -> None:
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
                profile_data = result_holder[0] or ""
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

    prompt = SOCIAL_ANALYSIS_PROMPT.replace("{{profile_data}}", profile_data[:15000])

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
