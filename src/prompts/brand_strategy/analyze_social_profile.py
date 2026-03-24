"""Prompt template for social media brand strategy analysis."""

SOCIAL_ANALYSIS_PROMPT = """Based on the social media profile data below, analyze the brand strategy:

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
