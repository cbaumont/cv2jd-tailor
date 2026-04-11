"""Tests for LaTeX validation utilities."""

from pathlib import Path

from cv2jd_tailor.latex_utils import (
    _check_unescaped_special_chars,
    parse_cv,
    validate_latex,
)
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


def test_mismatched_environment_names():
    tex = r"""
\begin{document}
\begin{itemize}
\item Hello
\end{enumerate}
\end{document}
"""
    issues = validate_latex(tex)
    errors = [i for i in issues if i.severity == "error"]
    assert any(
        "itemize" in i.message and "enumerate" in i.message for i in errors
    )


def test_stray_end_without_begin():
    tex = r"""
\end{itemize}
"""
    issues = validate_latex(tex)
    errors = [i for i in issues if i.severity == "error"]
    assert any("without matching" in i.message for i in errors)


def test_extra_closing_brace_flagged():
    tex = r"\section{Hello}} extra"
    issues = validate_latex(tex)
    errors = [i for i in issues if i.severity == "error"]
    assert any("Unmatched closing brace" in i.message for i in errors)


def test_unescaped_ampersand_warns_on_text_line():
    issues = _check_unescaped_special_chars("Research & development at Acme")
    assert any(
        i.severity == "warning" and "&" in i.message for i in issues
    )


def test_ampersand_in_tabular_row_allowed():
    # Lines containing '\\' are treated as tabular/align rows and skipped
    issues = _check_unescaped_special_chars("col1 & col2 \\\\")
    assert issues == []


def test_comment_lines_skipped_by_special_char_check():
    issues = _check_unescaped_special_chars("% this & that in a comment")
    assert issues == []


def test_parse_cv_without_document_env():
    tex = "\\section{Header}\n\\item one\n\\item two\n"
    cv = parse_cv(tex)
    assert cv.preamble == ""
    assert any(s.name == "Header" for s in cv.sections)


def test_parse_cv_no_sections_treats_body_as_one_section():
    tex = "\\begin{document}\n\\item lonely bullet\n\\end{document}\n"
    cv = parse_cv(tex)
    assert len(cv.sections) == 1
    assert cv.sections[0].name == "(body)"
    assert "lonely bullet" in cv.sections[0].bullets[0]


def test_parse_cv_captures_header_before_first_section():
    tex = (
        "\\begin{document}\n"
        "\\makecvtitle\n"
        "Some intro text\n"
        "\\section{Experience}\n"
        "\\item did things\n"
    )
    cv = parse_cv(tex)
    names = [s.name for s in cv.sections]
    assert "(header)" in names
    assert "Experience" in names


def test_validate_cv_latex_flags_broken_tex():
    tex = "\\begin{document}\n\\begin{itemize}\n\\item x\n\\end{document}\n"
    is_valid, issues = validate_cv_latex(tex)
    assert not is_valid
    assert any(i.severity == "error" for i in issues)
