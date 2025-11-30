"""Runner: Orchestrates the daily article aggregation pipeline.

This is the main entry point that coordinates:
1. Fetching articles from RSS sources
2. Analyzing articles with LLM (structured output - 1 call instead of 4!)
3. Generating LinkedIn post drafts
4. Building and sending daily digest email
"""

import logging


from .config import settings
from .db import engine, SessionLocal
from .models import Base, PostDraft
from .scrapers.orchestrator import fetch_all_sources
from .scrapers.blog import fetch_article
from .scrapers.markdown_extractor import convert_url_to_markdown
from .llm.client import analyze_article  # New: single structured call
from .email.sender import build_and_send_digest


# Configure logging with clear format for debugging
# Set root logger to INFO to suppress verbose third-party logs
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Set our app logger to DEBUG if enabled
logger = logging.getLogger(__name__)
log_level = logging.DEBUG if settings.DEBUG else logging.INFO
logger.setLevel(log_level)

# Suppress verbose logs from third-party libraries
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("docling").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.INFO)  # Keep OpenAI at INFO for API tracking


def run_once():
    """Main workflow: fetch RSS articles → summarize → create post drafts → build digest."""

    logger.info("=" * 70)
    logger.info("STARTING: Daily article aggregation pipeline")
    logger.info("=" * 70)

    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)
    logger.debug("✓ Database tables ready")

    with SessionLocal() as session:
        # STEP 1: Fetch articles from all sources
        logger.info("\n[STEP 1/3] FETCHING: Fetching articles from all sources...")
        logger.info("-" * 70)
        
        new_articles = fetch_all_sources(session, hours_lookback=48)
        
        if new_articles:
            logger.info(f"\n✓ Fetched {len(new_articles)} new articles total")
        else:
            logger.info("\n✓ No new articles found")

        # STEP 2: Summarize new articles and generate post drafts
        logger.info(
            "\n[STEP 2/3] PROCESSING: Summarizing articles and generating posts..."
        )
        logger.info("-" * 70)

        if not new_articles:
            logger.warning("No new articles to process.")
        else:
            logger.info(f"Processing {len(new_articles)} new articles\n")

            for idx, art in enumerate(new_articles, 1):
                logger.info(f"  [{idx}/{len(new_articles)}] {art.title[:60]}")

                # Try to extract markdown (optional enhancement) if not already done
                if not art.markdown_content:
                    try:
                        markdown_content = convert_url_to_markdown(art.url)
                        if markdown_content:
                            art.markdown_content = markdown_content
                            logger.debug(
                                f"        ✓ Markdown extracted ({len(markdown_content)} chars)"
                            )
                    except Exception as e:
                        logger.debug(
                            f"        - Markdown extraction skipped ({str(e)[:50]})"
                        )

                # Fetch article content for summarization
                source_text = art.markdown_content or art.content or ""
                if not source_text:
                    try:
                        fetched = fetch_article(art.url)
                        if fetched:
                            source_text = (
                                fetched.get("content") or fetched.get("excerpt") or ""
                            )
                            logger.debug(
                                f"        ✓ Article content fetched ({len(source_text)} chars)"
                            )
                    except Exception as e:
                        logger.warning(
                            f"        ✗ Could not fetch content: {str(e)[:80]}"
                        )

                if not source_text:
                    logger.warning("        ✗ No content available for analysis")
                    continue

                # 🎯 SINGLE STRUCTURED LLM CALL - Get everything at once
                # This replaces 4 separate API calls with 1 structured output call:
                # - Summary (was: summarize())
                # - Key concept (was: _call_llm in generator.py)
                # - LinkedIn post (was: _call_llm in generator.py)  
                # - Layman explanation (was: _call_llm in generator.py)
                try:
                    logger.debug("        → Calling OpenAI API for structured analysis...")
                    analysis = analyze_article(source_text)
                    
                    if not analysis:
                        logger.error("        ✗ Analysis failed (no result)")
                        continue
                    
                    # Update article with summary
                    art.summary = analysis.summary
                    art.snippet = analysis.summary.split("\n")[0][:200]
                    art.status = "processed"
                    session.add(art)
                    session.commit()
                    logger.info(f"        ✓ Analyzed: {art.snippet[:60]}")
                    
                    # Helper to remove NUL bytes which crash Postgres
                    def sanitize_text(text):
                        if isinstance(text, str):
                            return text.replace("\x00", "")
                        return text

                    # Create post draft with all the structured data
                    pd = PostDraft(
                        article_id=art.id,
                        post_content=sanitize_text(analysis.linkedin_post),
                        x_post=sanitize_text(analysis.x_post),
                        layman_explanation=sanitize_text(analysis.layman_explanation),
                        key_concept=sanitize_text(analysis.key_concept),
                        prompt_version="v3-enhanced",  # Enhanced prompts with X post
                        model="gpt-4o-mini",
                        status="draft",
                    )
                    session.add(pd)
                    session.commit()
                    logger.info(f"        ✓ Post draft created (ID: {pd.id[:8]}...)")
                    
                except Exception as e:
                    logger.error(f"        ✗ Analysis failed: {str(e)[:80]}")
                    continue

    # STEP 3: Build and send digest email
    logger.info("\n[STEP 3/3] DIGEST: Building and sending daily summary...")
    logger.info("-" * 70)

    # New signature handles its own session and logging
    build_and_send_digest()
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ Pipeline completed successfully!")
    logger.info("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        run_once()
    except Exception as e:
        logger.critical(f"FATAL ERROR: {e}", exc_info=True)
        raise
