from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    Integer,
    JSON,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


def utc_now():
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class Source(Base):
    __tablename__ = "sources"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'youtube' or 'blog'
    url = Column(String, nullable=False)
    feed_url = Column(String)
    meta = Column(JSON, default={})
    added_at = Column(DateTime, default=utc_now)
    last_fetched_at = Column(DateTime)
    active = Column(Boolean, default=True)


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("url", name="uq_articles_url"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    source_id = Column(String, ForeignKey("sources.id"), nullable=False)
    source_item_id = Column(String)  # source-specific id (video id, slug, etc.)
    url = Column(String, nullable=False, index=True)
    title = Column(String)
    author = Column(String)
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, default=utc_now)
    content = Column(Text)
    excerpt = Column(Text)
    summary = Column(Text)
    snippet = Column(String)
    markdown_content = Column(
        Text
    )  # Docling-extracted Markdown for better LLM processing
    tokens_est = Column(Integer, default=0)
    status = Column(String, default="new")  # new, processed, failed
    meta = Column(JSON, default={})

    source = relationship("Source")


class PostDraft(Base):
    __tablename__ = "post_drafts"

    id = Column(String, primary_key=True, default=gen_uuid)
    article_id = Column(String, ForeignKey("articles.id"), nullable=False)
    post_content = Column(Text)  # LinkedIn post
    x_post = Column(Text)  # X/Twitter post
    layman_explanation = Column(Text)
    key_concept = Column(String)  # Single most important idea from article
    status = Column(String, default="draft")  # draft, emailed, posted
    prompt_version = Column(String)
    model = Column(String)
    created_at = Column(DateTime, default=utc_now)

    article = relationship("Article")
