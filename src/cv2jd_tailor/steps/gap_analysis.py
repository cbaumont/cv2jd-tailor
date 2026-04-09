"""Step 3: Gap analysis — compare CV against job description."""

from __future__ import annotations

import json

from cv2jd_tailor.latex_utils import ParsedCV
from cv2jd_tailor.llm.base import LLMBackend
from cv2jd_tailor.prompts.gap_analysis import SYSTEM, format_gap_analysis_prompt
from cv2jd_tailor.steps.fetch_jd import JobDescription


def run_gap_analysis(
    cv: ParsedCV, jd: JobDescription, llm: LLMBackend
) -> dict:
    """Run gap analysis comparing the CV against the job description.

    Returns the parsed JSON gap analysis result.
    """
    # Format CV sections for the prompt
    cv_sections_text = _format_cv_sections(cv)

    user_prompt = format_gap_analysis_prompt(
        jd_text=jd.raw_text, cv_sections_text=cv_sections_text
    )

    response = llm.complete(system=SYSTEM, user=user_prompt)

    # Extract JSON from the response (may be wrapped in ```json blocks)
    return _parse_json_response(response)


def _format_cv_sections(cv: ParsedCV) -> str:
    """Format CV sections into a readable text block."""
    parts: list[str] = []
    for section in cv.sections:
        parts.append(f"### {section.name}")
        if section.bullets:
            for bullet in section.bullets:
                parts.append(f"  - {bullet}")
        else:
            # Show raw content (trimmed) for sections without bullets
            raw_preview = section.raw.strip()[:500]
            parts.append(f"  {raw_preview}")
        parts.append("")
    return "\n".join(parts)


def _parse_json_response(response: str) -> dict:
    """Extract and parse JSON from an LLM response."""
    # Try to find JSON block in markdown code fence
    json_str = _extract_fenced_block(response, "```json")
    if json_str is None:
        json_str = _extract_fenced_block(response, "```")
    if json_str is None:
        json_str = response.strip()

    return json.loads(json_str)


def _extract_fenced_block(text: str, opener: str) -> str | None:
    """Extract content from a fenced code block, or None if not found."""
    idx = text.find(opener)
    if idx == -1:
        return None
    start = idx + len(opener)
    end = text.find("```", start)
    if end == -1:
        # No closing fence — take everything after the opener
        return text[start:].strip()
    return text[start:end].strip()
