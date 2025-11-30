"""DEPRECATED: Prompt templates no longer used.

The prompts from this file have been moved to Pydantic Field descriptions
in app/llm/schemas.py as part of OpenAI's structured outputs feature.

Old prompts:
- EXTRACT_KEY_CONCEPT → ArticleAnalysis.key_concept Field description
- LINKEDIN_POST_TEMPLATE → ArticleAnalysis.linkedin_post Field description  
- LAYMAN_EXPLAIN_TEMPLATE → ArticleAnalysis.layman_explanation Field description

The new approach uses Pydantic Field descriptions which OpenAI's structured
output API uses to guide generation, providing better type safety and validation.

This file is kept for reference only and will be removed in a future version.

Migration complete: 2025-11-30
"""

# All prompts moved to app/llm/schemas.py as Field descriptions
