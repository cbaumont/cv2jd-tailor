"""Tests for reading CV files."""

from pathlib import Path

import pytest

from cv2jd_tailor.steps.read_cv import read_cv

FIXTURES = Path(__file__).parent / "fixtures"


def test_read_cv_parses_sample_fixture():
    cv = read_cv(FIXTURES / "sample_cv.tex")
    section_names = [s.name for s in cv.sections]
    assert "Experience" in section_names
    assert cv.raw.startswith("\\documentclass")


def test_read_cv_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        read_cv(tmp_path / "does_not_exist.tex")


def test_read_cv_wrong_suffix(tmp_path: Path):
    wrong = tmp_path / "cv.md"
    wrong.write_text("# not latex")
    with pytest.raises(ValueError, match="Expected a .tex file"):
        read_cv(wrong)


def test_read_cv_accepts_path_as_string():
    cv = read_cv(str(FIXTURES / "sample_cv.tex"))
    assert cv.preamble
