"""Tests for job description fetching."""

from cv2jd_tailor.steps.fetch_jd import _extract_text, _extract_title

from bs4 import BeautifulSoup


def test_extract_title_from_h1():
    html = "<html><body><h1>Senior Engineer</h1><p>Details</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    assert _extract_title(soup) == "Senior Engineer"


def test_extract_title_from_class():
    html = '<html><body><div class="job-title">ML Engineer</div></body></html>'
    soup = BeautifulSoup(html, "html.parser")
    assert _extract_title(soup) == "ML Engineer"


def test_extract_text_removes_scripts():
    html = """
    <html><body>
    <script>var x = 1;</script>
    <style>.hidden{display:none}</style>
    <p>Job description here</p>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = _extract_text(soup)
    assert "var x" not in text
    assert "Job description here" in text


def test_extract_text_collapses_whitespace():
    html = """
    <html><body>
    <p>Line one</p>



    <p>Line two</p>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    text = _extract_text(soup)
    # No more than 2 consecutive newlines
    assert "\n\n\n" not in text
