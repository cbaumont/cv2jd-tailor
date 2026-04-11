"""Integration tests for the pipeline (using a mock LLM)."""

from pathlib import Path

import httpx
import pytest

from cv2jd_tailor.llm.base import LLMBackend
from cv2jd_tailor.pipeline import run_pipeline
from cv2jd_tailor.steps import fetch_jd as fetch_jd_module
from cv2jd_tailor.steps.fetch_jd import JobDescription, fetch_jd
from cv2jd_tailor.steps.gap_analysis import (
    _format_cv_sections,
    _parse_json_response,
    run_gap_analysis,
)
from cv2jd_tailor.latex_utils import parse_cv
from cv2jd_tailor.steps.rewrite import rewrite_cv
from cv2jd_tailor.steps.save_report import _format_report

FIXTURES = Path(__file__).parent / "fixtures"


class MockLLM(LLMBackend):
    """Mock LLM that returns canned responses."""

    def __init__(self):
        self.call_count = 0

    def complete(self, system: str, user: str) -> str:
        self.call_count += 1
        return """```json
{
  "fit_score": 72,
  "strong_matches": [
    {"section": "Experience", "bullet": "Led migration of monolithic application to microservices architecture", "reason": "Directly relevant to role"}
  ],
  "bullets_to_improve": [
    {
      "section": "Experience",
      "original_bullet": "Built RESTful APIs serving 50K daily active users with 99.9\\\\% uptime",
      "suggestion": "Designed cloud-native RESTful APIs serving 50K daily active users with 99.9\\\\% uptime",
      "target_jd_requirement": "Cloud architecture experience",
      "impact": "high"
    }
  ],
  "keywords_to_add": ["cloud-native", "scalability"],
  "summary_update_needed": false,
  "summary_suggestion": null
}
```"""


def test_parse_json_from_code_fence():
    response = '```json\n{"fit_score": 85}\n```'
    result = _parse_json_response(response)
    assert result["fit_score"] == 85


def test_parse_json_bare():
    response = '{"fit_score": 85}'
    result = _parse_json_response(response)
    assert result["fit_score"] == 85


def test_parse_json_unclosed_fence():
    response = '```json\n{"fit_score": 90}\n'
    result = _parse_json_response(response)
    assert result["fit_score"] == 90


def test_rewrite_applies_bullet_replacement():
    original = (
        "\\section{Experience}\n"
        "\\item Built RESTful APIs serving 50K daily active users with 99.9\\% uptime\n"
        "\\item Mentored team of 4 junior engineers\n"
    )
    gap = {
        "bullets_to_improve": [
            {
                "original_bullet": "Built RESTful APIs serving 50K daily active users with 99.9\\% uptime",
                "suggestion": "Designed cloud-native RESTful APIs serving 50K daily active users with 99.9\\% uptime",
            }
        ]
    }
    result = rewrite_cv(original, gap)
    assert "Designed cloud-native RESTful APIs" in result
    assert "Built RESTful APIs" not in result
    assert "Mentored team of 4 junior engineers" in result


def test_rewrite_preserves_cv_structure_exactly():
    original = FIXTURES.joinpath("sample_cv.tex").read_text()
    gap = {
        "bullets_to_improve": [
            {
                "original_bullet": "Mentored team of 4 junior engineers through code reviews and pair programming sessions",
                "suggestion": "Mentored a team of 4 junior engineers via structured code reviews and pair programming",
            }
        ]
    }
    result = rewrite_cv(original, gap)
    assert "\\begin{document}" in result
    assert "\\end{document}" in result
    assert "\\section{Experience}" in result
    assert "\\section{Education}" in result
    assert "\\section{Skills}" in result
    assert result.count("\\begin{itemize}") == original.count("\\begin{itemize}")
    assert result.count("\\end{itemize}") == original.count("\\end{itemize}")
    assert "Mentored a team of 4 junior engineers" in result


def test_rewrite_skips_missing_original_bullet():
    original = "\\item Built RESTful APIs\n"
    gap = {
        "bullets_to_improve": [
            {
                "original_bullet": "Nonexistent bullet text",
                "suggestion": "Shiny new text",
            }
        ]
    }
    result = rewrite_cv(original, gap)
    assert result == original


def test_rewrite_applies_summary_update_starred_section():
    original = (
        "\\section*{Summary}\n"
        "\n"
        "Experienced engineer with 5 years of expertise.\n"
        "\n"
        "\\section*{Experience}\n"
    )
    gap = {
        "bullets_to_improve": [],
        "summary_update_needed": True,
        "summary_suggestion": "Senior cloud-native engineer with 5 years of backend expertise.",
    }
    result = rewrite_cv(original, gap)
    assert "Senior cloud-native engineer" in result
    assert "Experienced engineer" not in result
    assert "\\section*{Experience}" in result


def test_rewrite_applies_summary_update_before_switchcolumn():
    original = (
        "\\section*{Summary}\n"
        "\n"
        "Old summary body text that spans multiple lines\n"
        "and wraps onto a second one.\n"
        "\n"
        "\\switchcolumn\n"
    )
    gap = {
        "summary_update_needed": True,
        "summary_suggestion": "Brand new summary.",
    }
    result = rewrite_cv(original, gap)
    assert "Brand new summary." in result
    assert "Old summary body" not in result
    assert "\\switchcolumn" in result


def test_rewrite_ignores_summary_when_flag_false():
    original = (
        "\\section*{Summary}\n"
        "\n"
        "Original summary text.\n"
        "\n"
        "\\section*{Experience}\n"
    )
    gap = {
        "summary_update_needed": False,
        "summary_suggestion": "New summary text.",
    }
    result = rewrite_cv(original, gap)
    assert result == original


def test_rewrite_handles_empty_gap():
    original = "\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}\n"
    assert rewrite_cv(original, {}) == original


def test_format_report():
    gap = {
        "fit_score": 72,
        "strong_matches": [
            {"section": "Experience", "reason": "Good match"}
        ],
        "bullets_to_improve": [
            {
                "section": "Experience",
                "original_bullet": "Built APIs",
                "suggestion": "Emphasize scale",
                "target_jd_requirement": "Cloud experience",
                "impact": "high",
            }
        ],
        "keywords_to_add": ["cloud-native"],
        "summary_update_needed": False,
    }
    report = _format_report(gap)
    assert "72/100" in report
    assert "Strong Matches" in report
    assert "Changes Made" in report
    assert "`cloud-native`" in report


def test_rewrite_applies_multiple_bullets():
    original = (
        "\\item Alpha original text\n"
        "\\item Beta original text\n"
        "\\item Gamma untouched\n"
    )
    gap = {
        "bullets_to_improve": [
            {
                "original_bullet": "Alpha original text",
                "suggestion": "Alpha improved text",
            },
            {
                "original_bullet": "Beta original text",
                "suggestion": "Beta improved text",
            },
        ]
    }
    result = rewrite_cv(original, gap)
    assert "Alpha improved text" in result
    assert "Beta improved text" in result
    assert "Gamma untouched" in result
    assert "Alpha original text" not in result
    assert "Beta original text" not in result


def test_rewrite_summary_update_without_summary_section_noop():
    original = "\\section{Experience}\n\\item only\n"
    gap = {
        "summary_update_needed": True,
        "summary_suggestion": "Would be a new summary.",
    }
    # No Summary section exists — rewrite should not touch the source
    assert rewrite_cv(original, gap) == original


def test_rewrite_summary_update_with_empty_suggestion_noop():
    original = (
        "\\section*{Summary}\n"
        "\n"
        "Old summary.\n"
        "\n"
        "\\section*{Experience}\n"
    )
    gap = {
        "summary_update_needed": True,
        "summary_suggestion": "   ",
    }
    assert rewrite_cv(original, gap) == original


def test_rewrite_skips_identical_suggestion():
    original = "\\item Same text\n"
    gap = {
        "bullets_to_improve": [
            {
                "original_bullet": "Same text",
                "suggestion": "Same text",
            }
        ]
    }
    assert rewrite_cv(original, gap) == original


def test_format_cv_sections_handles_bullets_and_raw_fallback():
    cv = parse_cv((FIXTURES / "sample_cv.tex").read_text())
    out = _format_cv_sections(cv)
    # Bullet path
    assert "- Built RESTful APIs" in out
    # Section headers
    assert "### Experience" in out
    assert "### Education" in out


def test_run_gap_analysis_uses_llm_and_parses_json():
    cv = parse_cv((FIXTURES / "sample_cv.tex").read_text())
    jd = JobDescription(
        url="https://example.com/job/1",
        title="Senior Backend Engineer",
        raw_text="We need a senior backend engineer with cloud experience.",
    )
    llm = MockLLM()
    gap = run_gap_analysis(cv, jd, llm)
    assert llm.call_count == 1
    assert gap["fit_score"] == 72
    assert gap["bullets_to_improve"][0]["impact"] == "high"


# ---------------------------------------------------------------------------
# fetch_jd with a stubbed httpx.get
# ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "boom", request=None, response=None  # type: ignore[arg-type]
            )


@pytest.fixture
def fake_httpx(monkeypatch: pytest.MonkeyPatch):
    """Replace httpx.get inside fetch_jd with a scripted stub."""
    calls: list[dict] = []

    def _factory(html: str, status_code: int = 200):
        def _fake_get(url, **kwargs):
            calls.append({"url": url, "kwargs": kwargs})
            return _FakeResponse(html, status_code=status_code)

        monkeypatch.setattr(fetch_jd_module.httpx, "get", _fake_get)
        return calls

    return _factory


def test_fetch_jd_extracts_title_and_text(fake_httpx):
    html = """
    <html><head><title>ignored</title></head><body>
    <h1>Staff Platform Engineer</h1>
    <nav>Home</nav>
    <script>var x=1;</script>
    <p>Build delightful developer tooling.</p>
    <footer>© Acme</footer>
    </body></html>
    """
    calls = fake_httpx(html)
    jd = fetch_jd("https://jobs.example.com/123")
    assert jd.title == "Staff Platform Engineer"
    assert "developer tooling" in jd.raw_text
    assert "var x" not in jd.raw_text
    assert "© Acme" not in jd.raw_text
    # URL and UA header plumbed through
    assert calls[0]["url"] == "https://jobs.example.com/123"
    assert "User-Agent" in calls[0]["kwargs"]["headers"]
    assert calls[0]["kwargs"]["follow_redirects"] is True


def test_fetch_jd_title_fallback_to_title_tag(fake_httpx):
    html = "<html><head><title>Posting — Backend</title></head><body><p>body</p></body></html>"
    fake_httpx(html)
    jd = fetch_jd("https://example.com")
    assert jd.title == "Posting — Backend"


def test_fetch_jd_title_fallback_unknown(fake_httpx):
    html = "<html><body><p>no title anywhere</p></body></html>"
    fake_httpx(html)
    jd = fetch_jd("https://example.com")
    assert jd.title == "(unknown title)"


def test_fetch_jd_raises_on_http_error(fake_httpx):
    fake_httpx("<html></html>", status_code=500)
    with pytest.raises(httpx.HTTPStatusError):
        fetch_jd("https://example.com")


# ---------------------------------------------------------------------------
# Full pipeline smoke test
# ---------------------------------------------------------------------------


def test_run_pipeline_end_to_end(tmp_path, fake_httpx):
    fake_httpx(
        "<html><body><h1>Senior Backend Engineer</h1>"
        "<p>Cloud-native microservices at scale.</p></body></html>"
    )
    llm = MockLLM()
    result = run_pipeline(
        cv_path=FIXTURES / "sample_cv.tex",
        job_url="https://jobs.example.com/42",
        llm=llm,
        output_dir=tmp_path,
    )
    assert llm.call_count == 1
    assert result.jd.title == "Senior Backend Engineer"
    assert result.gap_analysis["fit_score"] == 72
    assert result.is_valid
    # Rewrite applied
    assert "Designed cloud-native RESTful APIs" in result.tailored_tex
    # Files saved with slug + timestamp naming
    assert result.cv_path is not None and result.cv_path.exists()
    assert result.report_path is not None and result.report_path.exists()
    assert result.cv_path.name.startswith("tailored_cv_senior-backend-engineer_")
    assert result.report_path.name.startswith("gap_report_senior-backend-engineer_")


def test_run_pipeline_dry_run_skips_save(tmp_path, fake_httpx):
    fake_httpx("<html><body><h1>Role</h1><p>stuff</p></body></html>")
    result = run_pipeline(
        cv_path=FIXTURES / "sample_cv.tex",
        job_url="https://example.com",
        llm=MockLLM(),
        output_dir=tmp_path,
        dry_run=True,
    )
    assert result.cv_path is None
    assert result.report_path is None
    # Nothing written into the output directory
    assert list(tmp_path.iterdir()) == []
