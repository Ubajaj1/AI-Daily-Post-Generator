"""OpenAI client with structured output support using gpt-4o-mini.

This module provides efficient article analysis using OpenAI's structured outputs
feature, reducing from 4 separate API calls to just 1 per article.

Model choice: gpt-4o-mini
- 80% cheaper than gpt-4o
- 60% cheaper than gpt-3.5-turbo  
- Better quality and reliability for structured outputs
- Perfect for our use case
"""

from typing import Optional
from openai import OpenAI
from ..config import settings
from .schemas import ArticleAnalysis

# Initialize OpenAI client
client = None
if settings.OPENAI_API_KEY:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)


def analyze_article(text: str, fallback: bool = True) -> Optional[ArticleAnalysis]:
    """Analyze article and return structured output with all content in ONE call.
    
    This replaces 4 separate LLM calls with a single structured output call:
    - Summary (was: summarize() function)
    - Key concept (was: _call_llm in generator.py)
    - LinkedIn post (was: _call_llm in generator.py)
    - Layman explanation (was: _call_llm in generator.py)
    
    Args:
        text: Article content (markdown or plain text)
        fallback: If True, return fallback data when API unavailable
    
    Returns:
        ArticleAnalysis object with all fields populated, or None if API fails
    
    Raises:
        Exception: If API call fails and fallback=False
    """
    if not client:
        if fallback:
            # Fallback: return basic truncated content
            truncated = text[:400] + ("..." if len(text) > 400 else "")
            return ArticleAnalysis(
                summary=truncated,
                key_concept="No API key configured",
                linkedin_post=f"Interesting article worth checking out:\n\n{truncated}",
                layman_explanation=truncated,
            )
        return None

    try:
        # Truncate text to avoid token limits (~8k chars ≈ ~2k tokens)
        article_text = text[:8000]
        
        response = client.responses.parse(
            model="gpt-4o-mini",  # Cheapest, fastest option with structured outputs
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert content analyzer and writer. "
                        "Your task is to analyze articles and create engaging content for different audiences. "
                        "Be concise, accurate, and compelling in all your outputs."
                    )
                },
                {
                    "role": "user",
                    "content": f"Analyze this article comprehensively:\n\n{article_text}"
                }
            ],
            text_format=ArticleAnalysis,
        )
        
        return response.output_parsed
        
    except Exception as e:
        # Log error and return fallback if enabled
        print(f"OpenAI API error during article analysis: {e}")
        if fallback:
            truncated = text[:400] + ("..." if len(text) > 400 else "")
            return ArticleAnalysis(
                summary=truncated,
                key_concept="Analysis failed - API error",
                linkedin_post=f"Check out this article:\n\n{truncated}",
                layman_explanation=truncated,
            )
        return None


# Legacy function for backward compatibility (deprecated)
def summarize(text: str, max_tokens: int = 300) -> str:
    """Legacy function - use analyze_article() instead for better efficiency.
    
    This function is maintained for backward compatibility but adds overhead
    by making a full structured API call and discarding most of the output.
    
    Deprecated: Use analyze_article() directly to get all content in one call.
    """
    analysis = analyze_article(text, fallback=True)
    return analysis.summary if analysis else text[:400]
