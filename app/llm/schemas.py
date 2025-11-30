"""Pydantic schemas for structured LLM outputs."""

from pydantic import BaseModel, Field


class ArticleAnalysis(BaseModel):
    """Structured output for complete article analysis.
    
    This combines summary, key concept, LinkedIn post, X post, and layman explanation
    into a single LLM call for maximum efficiency and consistency.
    """
    
    summary: str = Field(
        description="Concise 2-3 sentence summary of the article suitable for digest emails"
    )
    
    key_concept: str = Field(
        description="The single most important idea from the article in one clear sentence"
    )
    
    linkedin_post: str = Field(
        description=(
            "Professional LinkedIn post (150-200 words) with this structure:\n"
            "1) Engaging hook (1 sentence + optional single emoji)\n"
            "2) Problem/Challenge statement (if applicable)\n"
            "3) Solution/Key insights (use bullet points with • for main points)\n"
            "4) Concrete example or implication\n"
            "5) Key takeaway\n"
            "6) Engaging question for discussion\n\n"
            "Style: Professional but conversational, technical yet accessible. "
            "Perspective: ALWAYS use Third-Person (e.g., 'Anthropic announced...', 'They are developing...'). "
            "NEVER use 'We', 'Us', or 'Our' as if you are the company. You are an industry analyst reporting on this news. "
            "Focus on value and insights, not hype. "
            "NO hashtags."
        )
    )
    
    x_post: str = Field(
        description=(
            "Concise X/Twitter post (under 260 characters to leave room for link):\n"
            "- Punchy, engaging language\n"
            "- Highlight 1-2 key points only\n"
            "- Use casual tech language (e.g., 'drops gems', 'game-changer')\n"
            "- NO link in the content (will be added separately)\n"
            "- Optional: 1 emoji maximum\n\n"
            "Example style: 'Anthropic drops gems on long-running AI agents: "
            "Initializer for setup + coding agent for incremental progress w/ testing. "
            "Solves context loss in complex tasks. Game-changer for AI reliability!'"
        )
    )
    
    layman_explanation: str = Field(
        description=(
            "Detailed explanation for non-technical readers (approx 200-300 words). "
            "Structure:\n"
            "1) Start with a relatable scenario or problem statement.\n"
            "2) Explain the solution simply, breaking it down into clear parts (e.g., 'The Setup', 'The Action').\n"
            "3) Conclude with a specific, dedicated 'Analogy' section (e.g., 'Analogy: Building a Lego Castle...') "
            "that maps the technical concepts to everyday situations.\n"
            "Tone: Friendly, accessible, and storytelling-oriented."
        )
    )
