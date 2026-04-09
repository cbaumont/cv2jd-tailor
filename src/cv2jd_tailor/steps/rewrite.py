"""Step 4: Rewrite targeted CV bullets using an LLM."""

from __future__ import annotations

import json

from cv2jd_tailor.llm.base import LLMBackend
from cv2jd_tailor.prompts.rewrite import SYSTEM, format_rewrite_prompt


def rewrite_cv(
    original_tex: str, gap_analysis: dict, llm: LLMBackend
) -> str:
    """Rewrite specific CV bullets based on the gap analysis.

    Returns the complete modified LaTeX source.
    """
    user_prompt = format_rewrite_prompt(
        original_tex=original_tex,
        gap_analysis_json=json.dumps(gap_analysis, indent=2),
    )

    response = llm.complete(system=SYSTEM, user=user_prompt)

    # Extract LaTeX from the response (may be wrapped in ```latex blocks)
    return _extract_latex(response)


def _extract_latex(response: str) -> str:
    """Extract LaTeX source from an LLM response."""
    # Try to find LaTeX block in markdown code fence
    for marker in ("```latex", "```tex"):
        if marker in response:
            start = response.index(marker) + len(marker)
            end = response.index("```", start)
            return response[start:end].strip()

    if "```" in response:
        start = response.index("```") + 3
        end = response.index("```", start)
        return response[start:end].strip()

    # Assume the whole response is LaTeX
    return response.strip()
