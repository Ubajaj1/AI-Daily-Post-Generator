"""Simple blog scraper using `httpx` and `beautifulsoup4`.

This is a basic extractor — for production consider `readability-lxml` or `newspaper3k`.
"""

from typing import Optional, Dict
import httpx
from bs4 import BeautifulSoup
from dateutil import parser as dateparser


def fetch_article(url: str) -> Optional[Dict]:
    # Use a browser-like User-Agent and accept headers to reduce simple bot blocks.
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = httpx.get(url, timeout=20.0, headers=headers)
        resp.raise_for_status()
    except Exception:
        # one retry without custom headers (network flakiness)
        try:
            resp = httpx.get(url, timeout=20.0)
            resp.raise_for_status()
        except Exception:
            return None

    html = resp.text
    soup = BeautifulSoup(html, "lxml")

    # Title
    title_tag = soup.find("meta", property="og:title") or soup.find("title")
    title = (
        title_tag.get("content")
        if title_tag and title_tag.has_attr("content")
        else (title_tag.text if title_tag else None)
    )

    # Publish date heuristics
    pub_date = None
    for name in ("article:published_time", "pubdate", "date"):
        tag = soup.find("meta", attrs={"property": name}) or soup.find(
            "meta", attrs={"name": name}
        )
        if tag and tag.has_attr("content"):
            try:
                pub_date = dateparser.parse(tag["content"])
                break
            except Exception:
                continue

    # Extract article text: prefer <article>, fallback to main text
    article = soup.find("article")
    if article:
        paragraphs = [p.get_text(strip=True) for p in article.find_all("p")]
    else:
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]

    content = "\n\n".join([p for p in paragraphs if p])
    excerpt = paragraphs[0] if paragraphs else ""

    return {
        "title": title,
        "url": url,
        "published": pub_date,
        "content": content,
        "excerpt": excerpt,
    }
