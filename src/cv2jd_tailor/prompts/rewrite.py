"""Prompt templates for CV rewriting (Step 4)."""

SYSTEM = """\
You are an expert CV writer and LaTeX editor. You rewrite specific bullet points \
in a LaTeX CV to better match a job description.

Rules:
- ONLY rewrite the bullets you are asked to rewrite — leave everything else untouched
- Mirror the JD's vocabulary and tone naturally (no keyword stuffing)
- Keep bullet length and style consistent with the original
- NEVER invent experience or skills not present in the original
- NEVER change the LaTeX template structure, preamble, or commands
- Preserve the candidate's authentic voice — just sharpen it
- Return the COMPLETE LaTeX source with only the specified bullets changed
"""

USER_TEMPLATE = """\
## Original LaTeX CV
```latex
{original_tex}
```

## Gap Analysis Results
{gap_analysis_json}

## Instructions
Rewrite ONLY the bullets identified in the gap analysis. Return the complete LaTeX \
source with your changes applied. Do not add any explanation — return only the LaTeX code.

Important:
- Keep all \\begin{{}} / \\end{{}} pairs intact
- Do not modify the preamble or document class
- Do not add or remove sections
- If summary_update_needed is true, update the professional summary as suggested
"""


def format_rewrite_prompt(original_tex: str, gap_analysis_json: str) -> str:
    """Format the user prompt for rewriting."""
    return USER_TEMPLATE.format(
        original_tex=original_tex, gap_analysis_json=gap_analysis_json
    )
