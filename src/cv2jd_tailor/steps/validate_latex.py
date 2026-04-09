"""Step 5: Validate LaTeX source for common issues."""

from __future__ import annotations

from cv2jd_tailor.latex_utils import ValidationIssue, validate_latex


def validate_cv_latex(tex: str) -> tuple[bool, list[ValidationIssue]]:
    """Validate a CV's LaTeX source.

    Returns (is_valid, issues) where is_valid is True if there are no errors
    (warnings are allowed).
    """
    issues = validate_latex(tex)
    errors = [i for i in issues if i.severity == "error"]
    return len(errors) == 0, issues
