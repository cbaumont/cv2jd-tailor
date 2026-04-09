"""Step 2: Fetch and extract a job description from a URL."""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup


@dataclass
class JobDescription:
    """Extracted job description content."""

    url: str
    title: str
    raw_text: str


def fetch_jd(url: str, timeout: float = 30.0) -> JobDescription:
    """Fetch a job posting URL and extract its text content."""
    response = httpx.get(
        url,
        follow_redirects=True,
        timeout=timeout,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; cv2jd-tailor/0.1; "
                "+https://github.com/cv2jd-tailor)"
            )
        },
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Extract title
    title = _extract_title(soup)

    # Extract main text content
    raw_text = _extract_text(soup)

    return JobDescription(url=url, title=title, raw_text=raw_text)


def _extract_title(soup: BeautifulSoup) -> str:
    """Try to extract the job title from the page."""
    # Try common patterns
    for selector in ["h1", "[class*='title']", "[class*='job-title']", "title"]:
        tag = soup.select_one(selector)
        if tag and tag.get_text(strip=True):
            return tag.get_text(strip=True)
    return "(unknown title)"


def _extract_text(soup: BeautifulSoup) -> str:
    """Extract clean text from HTML, collapsing whitespace."""
    text = soup.get_text(separator="\n")
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(lines).strip()
