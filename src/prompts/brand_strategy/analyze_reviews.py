"""Prompt template for customer review sentiment analysis."""

REVIEW_ANALYSIS_PROMPT = """Analyze the following customer reviews for {{business_name}}.
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
