"""Tests for LaTeX validation utilities."""

from pathlib import Path

from cv2jd_tailor.latex_utils import parse_cv, validate_latex
from cv2jd_tailor.steps.validate_latex import validate_cv_latex

FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_cv_passes_validation():
    tex = (FIXTURES / "sample_cv.tex").read_text()
    is_valid, issues = validate_cv_latex(tex)
    errors = [i for i in issues if i.severity == "error"]
    assert is_valid, f"Expected valid CV, got errors: {errors}"


def test_unmatched_begin():
    tex = r"""
\begin{document}
\begin{itemize}
\item Hello
\end{document}
"""
    issues = validate_latex(tex)
    errors = [i for i in issues if i.severity == "error"]
    assert any("itemize" in i.message for i in errors)


def test_unmatched_end():
    tex = r"""
\begin{document}
\end{itemize}
\end{document}
"""
    issues = validate_latex(tex)
    errors = [i for i in issues if i.severity == "error"]
    assert any("itemize" in i.message for i in errors)


def test_unmatched_brace():
    tex = r"""
\begin{document}
\section{Unclosed
\end{document}
"""
    issues = validate_latex(tex)
    errors = [i for i in issues if i.severity == "error"]
    assert any("brace" in i.message.lower() for i in errors)


def test_balanced_braces_pass():
    tex = r"\section{Hello} \textbf{world}"
    issues = validate_latex(tex)
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0


def test_parse_cv_extracts_sections():
    tex = (FIXTURES / "sample_cv.tex").read_text()
    cv = parse_cv(tex)
    section_names = [s.name for s in cv.sections]
    assert "Professional Summary" in section_names
    assert "Experience" in section_names
    assert "Education" in section_names
    assert "Skills" in section_names


def test_parse_cv_extracts_preamble():
    tex = (FIXTURES / "sample_cv.tex").read_text()
    cv = parse_cv(tex)
    assert r"\documentclass" in cv.preamble
    assert r"\begin{document}" in cv.preamble


def test_parse_cv_extracts_bullets():
    tex = (FIXTURES / "sample_cv.tex").read_text()
    cv = parse_cv(tex)
    exp_section = next(s for s in cv.sections if s.name == "Experience")
    assert len(exp_section.bullets) >= 3
