"""Step 6: Save tailored CV and gap report."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def save_outputs(
    tailored_tex: str,
    gap_analysis: dict,
    output_dir: str | Path = "output",
    jd_title: str | None = None,
) -> tuple[Path, Path]:
    """Save the tailored CV and gap report to the output directory.

    Filenames include a slug derived from the JD title plus a timestamp so
    successive runs never overwrite previous outputs.

    Returns (cv_path, report_path).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    suffix = _build_suffix(jd_title)

    cv_path = out / f"tailored_cv_{suffix}.tex"
    cv_path.write_text(tailored_tex, encoding="utf-8")

    report_path = out / f"gap_report_{suffix}.md"
    report_path.write_text(_format_report(gap_analysis), encoding="utf-8")

    return cv_path, report_path


def _build_suffix(jd_title: str | None) -> str:
    """Build a filename suffix from a JD title and the current timestamp.

    The timestamp includes microseconds so that two runs in the same second
    still produce distinct filenames.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    slug = _slugify(jd_title) if jd_title else ""
    return f"{slug}_{timestamp}" if slug else timestamp


def _slugify(value: str, max_length: int = 60) -> str:
    """Normalise a string to a safe, lowercase, hyphen-separated slug."""
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    if len(value) > max_length:
        value = value[:max_length].rstrip("-")
    return value


def _format_report(gap: dict) -> str:
    """Format the gap analysis into a readable markdown report."""
    lines: list[str] = []
    lines.append("# CV Tailoring Report")
    lines.append("")

    # Fit score
    score = gap.get("fit_score", "N/A")
    lines.append(f"## Fit Score: {score}/100")
    lines.append("")

    # Strong matches
    strong = gap.get("strong_matches", [])
    if strong:
        lines.append("## Strong Matches (unchanged)")
        lines.append("")
        for m in strong:
            lines.append(f"- **{m.get('section', '?')}**: {m.get('reason', '')}")
        lines.append("")

    # Changes made
    bullets = gap.get("bullets_to_improve", [])
    if bullets:
        lines.append("## Changes Made")
        lines.append("")
        for b in bullets:
            lines.append(f"### {b.get('section', '?')} ({b.get('impact', '?')} impact)")
            lines.append(f"- **Original**: {b.get('original_bullet', '')}")
            lines.append(f"- **Suggestion**: {b.get('suggestion', '')}")
            lines.append(f"- **Targets**: {b.get('target_jd_requirement', '')}")
            lines.append("")

    # Keywords
    keywords = gap.get("keywords_to_add", [])
    if keywords:
        lines.append("## Keywords Added")
        lines.append("")
        lines.append(", ".join(f"`{k}`" for k in keywords))
        lines.append("")

    # Summary update
    if gap.get("summary_update_needed"):
        lines.append("## Summary Updated")
        lines.append("")
        lines.append(gap.get("summary_suggestion", ""))
        lines.append("")

    return "\n".join(lines)
