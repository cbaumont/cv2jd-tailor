"""Prompt templates for gap analysis (Step 3)."""

SYSTEM = """\
You are an expert CV analyst. You compare a candidate's CV against a job description \
and produce a structured gap analysis.

Rules:
- Be specific — reference exact bullet points and JD requirements
- Score the current fit honestly (0-100)
- Identify up to 8 bullets to improve, prioritized by impact
- Identify strong matches that should NOT be changed
- List keywords from the JD that should be woven into the CV naturally
- NEVER suggest inventing experience or skills not present in the CV
"""

USER_TEMPLATE = """\
## Job Description
{jd_text}

## CV Sections
{cv_sections}

## Instructions
Analyze the CV against the job description and respond in this exact JSON format:

```json
{{
  "fit_score": <0-100>,
  "strong_matches": [
    {{"section": "<section name>", "bullet": "<bullet text>", "reason": "<why it's a match>"}}
  ],
  "bullets_to_improve": [
    {{
      "section": "<section name>",
      "original_bullet": "<exact original text>",
      "suggestion": "<how to improve it>",
      "target_jd_requirement": "<which JD requirement this addresses>",
      "impact": "<high|medium|low>"
    }}
  ],
  "keywords_to_add": ["<keyword1>", "<keyword2>"],
  "summary_update_needed": <true|false>,
  "summary_suggestion": "<suggested update if needed, else null>"
}}
```
"""


def format_gap_analysis_prompt(jd_text: str, cv_sections_text: str) -> str:
    """Format the user prompt for gap analysis."""
    return USER_TEMPLATE.format(jd_text=jd_text, cv_sections=cv_sections_text)
