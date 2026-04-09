"""MCP server exposing cv2jd-tailor tools."""

from __future__ import annotations

import json
import os

from fastmcp import FastMCP

from cv2jd_tailor.latex_utils import validate_latex
from cv2jd_tailor.llm.litellm_backend import LiteLLMBackend
from cv2jd_tailor.pipeline import run_pipeline
from cv2jd_tailor.steps.fetch_jd import fetch_jd
from cv2jd_tailor.steps.gap_analysis import run_gap_analysis
from cv2jd_tailor.steps.read_cv import read_cv

mcp = FastMCP("cv2jd-tailor")


def _get_llm() -> LiteLLMBackend:
    model = os.environ.get("CV2JD_MODEL")
    if not model:
        raise ValueError("CV2JD_MODEL environment variable must be set")
    temperature = float(os.environ.get("CV2JD_TEMPERATURE", "0.3"))
    return LiteLLMBackend(model=model, temperature=temperature)


@mcp.tool()
def tailor_cv(
    cv_path: str,
    job_url: str,
    output_dir: str = "output",
) -> str:
    """Tailor a LaTeX CV for a specific job posting.

    Runs the full 6-step pipeline: read CV, fetch JD, gap analysis,
    rewrite bullets, validate LaTeX, and save outputs.

    Args:
        cv_path: Path to the LaTeX CV file (.tex)
        job_url: URL of the job posting
        output_dir: Directory to save outputs (default: "output")
    """
    llm = _get_llm()
    result = run_pipeline(cv_path=cv_path, job_url=job_url, llm=llm, output_dir=output_dir)

    summary = {
        "fit_score": result.gap_analysis.get("fit_score"),
        "bullets_rewritten": len(result.gap_analysis.get("bullets_to_improve", [])),
        "latex_valid": result.is_valid,
        "cv_saved_to": str(result.cv_path),
        "report_saved_to": str(result.report_path),
    }
    return json.dumps(summary, indent=2)


@mcp.tool()
def validate_cv_latex(tex_content: str) -> str:
    """Validate LaTeX source for common issues.

    Checks for unmatched environments, unbalanced braces, and
    unescaped special characters.

    Args:
        tex_content: The LaTeX source code to validate
    """
    issues = validate_latex(tex_content)
    if not issues:
        return "No issues found."

    lines = []
    for issue in issues:
        prefix = "ERROR" if issue.severity == "error" else "WARN"
        lines.append(f"[{prefix}] Line {issue.line}: {issue.message}")

    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    lines.append(f"\n{errors} error(s), {warnings} warning(s)")
    return "\n".join(lines)


@mcp.tool()
def analyze_gap(cv_path: str, job_url: str) -> str:
    """Run gap analysis only — compare a CV against a job description.

    Does NOT rewrite the CV. Returns the gap analysis as JSON.

    Args:
        cv_path: Path to the LaTeX CV file (.tex)
        job_url: URL of the job posting
    """
    llm = _get_llm()
    cv = read_cv(cv_path)
    jd = fetch_jd(job_url)
    gap = run_gap_analysis(cv, jd, llm)
    return json.dumps(gap, indent=2)
