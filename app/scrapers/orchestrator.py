"""Scraper orchestrator: Unified interface for fetching articles from all sources.

This module provides a clean API for the runner to fetch articles without
duplicating scraping logic.
"""

import datetime
from datetime import timedelta, timezone
from typing import List
import logging

from dateutil import parser as dateparser
from feedparser import parse as feedparse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Source, Article
from ..sources.registry import SOURCES
from .markdown_extractor import convert_url_to_markdown

logger = logging.getLogger(__name__)


def ensure_source_registered(session: Session, source_config: dict) -> Source:
    """Ensure a source exists in the database, creating if needed.
    
    Args:
        session: SQLAlchemy session
        source_config: Dict with 'name', 'type', 'url', 'feed_url'
    
    Returns:
        Source object (existing or newly created)
    """
    stmt = select(Source).where(Source.url == source_config["url"])
    existing = session.execute(stmt).scalars().first()

    if not existing:
        src = Source(
            name=source_config["name"],
            type=source_config["type"],
            url=source_config["url"],
            feed_url=source_config.get("feed_url"),
        )
        session.add(src)
        session.commit()
        logger.info(f"  ✓ Registered: {src.name}")
        return src
    else:
        logger.debug(f"  - Already registered: {existing.name}")
        return existing


def fetch_articles_from_rss(
    session: Session,
    source: Source,
    feed_url: str,
    hours_lookback: int = 48
) -> List[Article]:
    """Fetch articles from an RSS feed and insert new ones into the database.
    
    Implements a fallback strategy: if no articles found within hours_lookback,
    fetches the 2 most recent articles regardless of date.
    
    Args:
        session: SQLAlchemy session
        source: Source object
        feed_url: RSS feed URL
        hours_lookback: Only fetch articles published within this many hours
    
    Returns:
        List of newly created Article objects
    """
    logger.info(f"\n  Fetching from: {source.name}")
    new_articles = []
    
    # Check if we have ever fetched from this source before
    # This prevents "backcrawling" on subsequent runs if no new articles exist
    source_has_history = session.query(Article.id).filter(Article.source_id == source.id).first() is not None
    
    try:
        feed = feedparse(feed_url)
        logger.debug(f"    Found {len(feed.entries)} articles in RSS feed")

        # Define cutoff for filtering articles
        cutoff = datetime.datetime.now(timezone.utc) - timedelta(hours=hours_lookback)
        logger.debug(f"    Filtering for articles published after: {cutoff}")

        recent_candidates = []  # Track recent articles for fallback
        
        for entry in feed.entries:
            url = entry.get("link")
            if not url:
                continue

            # Parse published date
            published = None
            if entry.get("published"):
                try:
                    published = dateparser.parse(entry.get("published"))
                    # If parsed datetime is naive, assume UTC
                    if published.tzinfo is None:
                        published = published.replace(tzinfo=timezone.utc)
                except Exception:
                    published = None

            # Check if article already exists
            exists_stmt = select(Article).where(Article.url == url)
            found = session.execute(exists_stmt).scalars().first()
            if found:
                logger.debug(
                    f"    - Article already in DB: {entry.get('title', 'untitled')[:50]}"
                )
                continue

            # Track for potential fallback (even if old)
            if published:
                recent_candidates.append((published, entry, url))

            # Skip articles older than cutoff for primary fetch
            if published and published < cutoff:
                logger.debug(
                    f"    - Skipping old article ({published.date()}): {entry.get('title', 'untitled')[:50]}"
                )
                continue

            # Skip if no published date is available
            if not published:
                logger.debug(
                    f"    - Skipping article without publish date: {entry.get('title', 'untitled')[:50]}"
                )
                continue

            # Create new article record
            art = Article(
                source_id=source.id,
                source_item_id=entry.get("id"),
                url=url,
                title=entry.get("title"),
                published_at=published,
                content=entry.get("summary") or entry.get("description") or None,
                status="new",
            )
            session.add(art)
            session.commit()

            # Try to extract markdown using Docling for better LLM results
            try:
                md = convert_url_to_markdown(art.url)
                if md:
                    art.markdown_content = md
                    session.add(art)
                    session.commit()
                    logger.debug("        ✓ Markdown extracted")
            except Exception as e:
                logger.debug(f"        - Markdown extraction skipped: {str(e)[:50]}")

            title_preview = entry.get("title", "untitled")[:55]
            logger.info(f"    ✓ NEW: {title_preview}")
            new_articles.append(art)

        # FALLBACK: Only run if no new articles AND this is a brand new source (no history)
        if not new_articles and recent_candidates and not source_has_history:
            logger.info(f"    📌 New source detected! Fetching 2 most recent articles...")
            
            # Sort by date descending and take top 2
            recent_candidates.sort(reverse=True, key=lambda x: x[0])
            
            for published, entry, url in recent_candidates[:2]:
                art = Article(
                    source_id=source.id,
                    source_item_id=entry.get("id"),
                    url=url,
                    title=entry.get("title"),
                    published_at=published,
                    content=entry.get("summary") or entry.get("description") or None,
                    status="new",
                )
                session.add(art)
                session.commit()

                # Try to extract markdown
                try:
                    md = convert_url_to_markdown(art.url)
                    if md:
                        art.markdown_content = md
                        session.add(art)
                        session.commit()
                        logger.debug("        ✓ Markdown extracted")
                except Exception as e:
                    logger.debug(f"        - Markdown extraction skipped: {str(e)[:50]}")

                title_preview = entry.get("title", "untitled")[:55]
                logger.info(f"    ✓ RECENT ({published.date()}): {title_preview}")
                new_articles.append(art)

    except Exception as e:
        logger.error(f"    ✗ Error fetching from {source.name}: {str(e)[:100]}")

    return new_articles


def fetch_all_sources(session: Session, hours_lookback: int = 48) -> List[Article]:
    """Fetch articles from all registered sources.
    
    Args:
        session: SQLAlchemy session
        hours_lookback: Only fetch articles published within this many hours
    
    Returns:
        List of all newly created Article objects across all sources
    """
    all_new_articles = []
    
    for source_config in SOURCES:
        # Ensure source is registered in database
        source = ensure_source_registered(session, source_config)
        
        # Fetch articles from RSS feed if applicable
        if source_config["type"] == "blog" and source_config.get("feed_url"):
            new_articles = fetch_articles_from_rss(
                session, 
                source, 
                source_config["feed_url"],
                hours_lookback
            )
            all_new_articles.extend(new_articles)
    
    return all_new_articles
