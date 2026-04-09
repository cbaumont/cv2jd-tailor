"""Step 6: Save tailored CV and gap report."""

from __future__ import annotations

from pathlib import Path


def save_outputs(
    tailored_tex: str,
    gap_analysis: dict,
    output_dir: str | Path = "output",
) -> tuple[Path, Path]:
    """Save the tailored CV and gap report to the output directory.

    Returns (cv_path, report_path).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    cv_path = out / "tailored_cv.tex"
    cv_path.write_text(tailored_tex, encoding="utf-8")

    report_path = out / "gap_report.md"
    report_path.write_text(_format_report(gap_analysis), encoding="utf-8")

    return cv_path, report_path


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
