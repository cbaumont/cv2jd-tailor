"""Integration tests for the pipeline (using a mock LLM)."""

from pathlib import Path

from cv2jd_tailor.llm.base import LLMBackend
from cv2jd_tailor.steps.gap_analysis import _parse_json_response
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
