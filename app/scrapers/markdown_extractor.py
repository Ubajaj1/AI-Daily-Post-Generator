"""Extract article content as Markdown using Docling for better LLM processing."""

import logging
from typing import Optional
import httpx
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


def convert_url_to_markdown(url: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch a URL and convert its main content to Markdown using Docling.

    Falls back to None if Docling is unavailable or conversion fails.

    Args:
        url: URL to extract and convert.
        timeout: HTTP request timeout in seconds.

    Returns:
        Markdown string if successful, None otherwise.
    """
    try:
        # Try to import docling
        try:
            from docling.document_converter import DocumentConverter
        except ImportError:
            logger.warning("docling not available; skipping markdown extraction")
            return None

        # Fetch the URL with browser-like headers
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        logger.debug(f"Fetching {url} for markdown extraction")
        response = httpx.get(
            url, headers=headers, timeout=timeout, follow_redirects=True
        )
        response.raise_for_status()

        # Use Docling to convert: write bytes to temp file, then convert
        converter = DocumentConverter()
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".html", delete=False
        ) as tmp:
            tmp.write(response.content)
            tmp_path = Path(tmp.name)

        try:
            result = converter.convert(tmp_path)
            # ConversionResult has a 'document' attribute which is a DoclingDocument
            # We need to export that to markdown
            markdown = None
            
            # Try to export from the document
            if hasattr(result, 'document'):
                doc = result.document
                try:
                    markdown = doc.export_to_markdown()
                except Exception:
                    pass

            # If that didn't work, try other methods on the result itself
            if not markdown:
                try:
                    markdown = result.export_to_markdown()
                except Exception:
                    pass

            if not markdown:
                logger.warning(f"Could not extract markdown from {url} - export failed")
                return None

            if markdown:
                logger.debug(f"Successfully extracted markdown for {url}")
                return markdown
        finally:
            tmp_path.unlink(missing_ok=True)

    except Exception as e:
        logger.warning(f"Failed to extract markdown from {url}: {e}")
        return None
