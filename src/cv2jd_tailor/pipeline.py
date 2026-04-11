"""Pipeline orchestrator — runs the full 6-step CV tailoring process."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cv2jd_tailor.latex_utils import ParsedCV
from cv2jd_tailor.llm.base import LLMBackend
from cv2jd_tailor.steps.fetch_jd import JobDescription, fetch_jd
from cv2jd_tailor.steps.gap_analysis import run_gap_analysis
from cv2jd_tailor.steps.read_cv import read_cv
from cv2jd_tailor.steps.rewrite import rewrite_cv
from cv2jd_tailor.steps.save_report import save_outputs
from cv2jd_tailor.steps.validate_latex import validate_cv_latex


@dataclass
class PipelineResult:
    """Result of a full pipeline run."""

    cv: ParsedCV
    jd: JobDescription
    gap_analysis: dict
    tailored_tex: str
    is_valid: bool
    validation_issues: list
    cv_path: Path | None = None
    report_path: Path | None = None


def run_pipeline(
    cv_path: str | Path,
    job_url: str,
    llm: LLMBackend,
    output_dir: str | Path = "output",
    dry_run: bool = False,
) -> PipelineResult:
    """Run the full CV tailoring pipeline.

    Steps:
    1. Read the CV
    2. Fetch the job description
    3. Run gap analysis
    4. Rewrite targeted bullets
    5. Validate the LaTeX
    6. Save outputs (unless dry_run)
    """
    # Step 1: Read CV
    cv = read_cv(cv_path)

    # Step 2: Fetch JD
    jd = fetch_jd(job_url)

    # Step 3: Gap analysis
    gap = run_gap_analysis(cv, jd, llm)

    # Step 4: Rewrite
    tailored_tex = rewrite_cv(cv.raw, gap)

    # Step 5: Validate
    is_valid, issues = validate_cv_latex(tailored_tex)

    result = PipelineResult(
        cv=cv,
        jd=jd,
        gap_analysis=gap,
        tailored_tex=tailored_tex,
        is_valid=is_valid,
        validation_issues=issues,
    )

    # Step 6: Save (unless dry run)
    if not dry_run:
        cv_out, report_out = save_outputs(tailored_tex, gap, output_dir)
        result.cv_path = cv_out
        result.report_path = report_out

    return result
