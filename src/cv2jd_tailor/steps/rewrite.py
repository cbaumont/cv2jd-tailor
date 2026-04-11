"""Step 4: Apply gap-analysis rewrites to the CV as targeted replacements."""

from __future__ import annotations

import re


SUMMARY_SECTION_RE = re.compile(
    r"(\\section\*?\s*\{Summary\}\s*)(.*?)(?=\\section\*?\s*\{|\\switchcolumn|\\end\{paracol\}|\\end\{document\})",
    re.DOTALL | re.IGNORECASE,
)


def rewrite_cv(original_tex: str, gap_analysis: dict) -> str:
    """Apply gap-analysis rewrites to the CV.

    Deterministic string replacement:
    - each bullet in bullets_to_improve: replace original_bullet with suggestion
    - summary (if summary_update_needed): locate the Summary section in the
      source and replace its body with summary_suggestion
    """
    tex = original_tex

    for bullet in gap_analysis.get("bullets_to_improve") or []:
        original = (bullet.get("original_bullet") or "").strip()
        suggestion = (bullet.get("suggestion") or "").strip()
        if not original or not suggestion or original == suggestion:
            continue
        if original in tex:
            tex = tex.replace(original, suggestion, 1)

    if gap_analysis.get("summary_update_needed"):
        new_summary = (gap_analysis.get("summary_suggestion") or "").strip()
        if new_summary:
            tex = _replace_summary(tex, new_summary)

    return tex


def _replace_summary(tex: str, new_summary: str) -> str:
    """Replace the body of the Summary section with new_summary, preserving
    the leading blank line and the trailing whitespace that separates it from
    the next section."""
    match = SUMMARY_SECTION_RE.search(tex)
    if not match:
        return tex
    header = match.group(1)
    body = match.group(2)
    trailing_ws = body[len(body.rstrip()):]
    leading_ws = body[: len(body) - len(body.lstrip())]
    replacement = f"{header}{leading_ws}{new_summary}{trailing_ws}"
    return tex[: match.start()] + replacement + tex[match.end():]
