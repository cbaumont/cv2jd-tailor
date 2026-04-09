"""Integration tests for the pipeline (using a mock LLM)."""

import json
from pathlib import Path

from cv2jd_tailor.llm.base import LLMBackend
from cv2jd_tailor.pipeline import run_pipeline
from cv2jd_tailor.steps.gap_analysis import _parse_json_response
from cv2jd_tailor.steps.rewrite import _extract_latex
from cv2jd_tailor.steps.save_report import _format_report

FIXTURES = Path(__file__).parent / "fixtures"


class MockLLM(LLMBackend):
    """Mock LLM that returns canned responses."""

    def __init__(self):
        self.call_count = 0

    def complete(self, system: str, user: str) -> str:
        self.call_count += 1
        if self.call_count == 1:
            # Gap analysis response
            return """```json
{
  "fit_score": 72,
  "strong_matches": [
    {"section": "Experience", "bullet": "Led migration of monolithic application to microservices architecture", "reason": "Directly relevant to role"}
  ],
  "bullets_to_improve": [
    {
      "section": "Experience",
      "original_bullet": "Built RESTful APIs serving 50K daily active users with 99.9% uptime",
      "suggestion": "Emphasize scalability and cloud-native approach",
      "target_jd_requirement": "Cloud architecture experience",
      "impact": "high"
    }
  ],
  "keywords_to_add": ["cloud-native", "scalability"],
  "summary_update_needed": false,
  "summary_suggestion": null
}
```"""
        else:
            # Rewrite response — return the original CV with minor change
            tex = FIXTURES.joinpath("sample_cv.tex").read_text()
            return f"```latex\n{tex}\n```"


# --- Unit tests for helper functions ---


def test_parse_json_from_code_fence():
    response = '```json\n{"fit_score": 85}\n```'
    result = _parse_json_response(response)
    assert result["fit_score"] == 85


def test_parse_json_bare():
    response = '{"fit_score": 85}'
    result = _parse_json_response(response)
    assert result["fit_score"] == 85


def test_extract_latex_from_code_fence():
    response = "```latex\n\\documentclass{article}\n```"
    result = _extract_latex(response)
    assert result == "\\documentclass{article}"


def test_extract_latex_bare():
    response = "\\documentclass{article}"
    result = _extract_latex(response)
    assert response == result


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
