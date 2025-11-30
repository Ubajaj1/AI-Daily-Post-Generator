"""Registry of blog RSS sources to fetch articles from.

Only active RSS feeds are included. Add new sources here as needed.
"""

SOURCES = [
    {
        "name": "Anthropic Engineering",
        "type": "blog",
        "url": "https://www.anthropic.com/engineering",
        "feed_url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
    },
    {
        "name": "Anthropic Research",
        "type": "blog",
        "url": "https://www.anthropic.com/research",
        "feed_url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
    },
    {
        "name": "Ars Technica",
        "type": "blog",
        "url": "https://arstechnica.com/",
        "feed_url": "https://feeds.arstechnica.com/arstechnica/index",
    },
    {
        "name": "Surge AI Blog",
        "type": "blog",
        "url": "https://www.surgehq.ai/blog",
        "feed_url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_blogsurgeai.xml",
    },
]
