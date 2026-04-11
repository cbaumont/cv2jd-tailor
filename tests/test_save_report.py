"""Tests for save_outputs, slug helpers, and report formatting."""

from pathlib import Path

from cv2jd_tailor.steps.save_report import (
    _build_suffix,
    _format_report,
    _slugify,
    save_outputs,
)


def test_slugify_basic():
    assert _slugify("Senior Backend Engineer") == "senior-backend-engineer"


def test_slugify_strips_punctuation_and_unicode():
    assert _slugify("Senior Backend Engineer (Remote) — EU") == (
        "senior-backend-engineer-remote-eu"
    )


def test_slugify_collapses_runs_of_separators():
    assert _slugify("foo   bar///baz") == "foo-bar-baz"


def test_slugify_truncates_and_trims_trailing_dash():
    # Construct input whose character-60 lands on a dash so the trim matters
    title = "a" * 58 + " " + "bbb"  # slug: 58 a's + '-' + 'bbb', length 62
    result = _slugify(title, max_length=59)
    assert len(result) <= 59
    assert not result.endswith("-")
    assert result == "a" * 58


def test_slugify_empty_string():
    assert _slugify("") == ""
    assert _slugify("—   ") == ""


def test_build_suffix_with_title():
    suffix = _build_suffix("Senior Backend Engineer")
    assert suffix.startswith("senior-backend-engineer_")
    # YYYYMMDD_HHMMSS_ffffff = 22 chars after slug + underscore
    timestamp = suffix.removeprefix("senior-backend-engineer_")
    assert len(timestamp) == len("YYYYMMDD_HHMMSS_ffffff")


def test_build_suffix_without_title():
    suffix = _build_suffix(None)
    assert len(suffix) == len("YYYYMMDD_HHMMSS_ffffff")
    assert "_" in suffix


def test_build_suffix_empty_title_falls_back_to_timestamp():
    suffix = _build_suffix("   ")
    # Slug is empty so suffix is bare timestamp
    assert len(suffix) == len("YYYYMMDD_HHMMSS_ffffff")


def test_save_outputs_writes_both_files(tmp_path: Path):
    gap = {"fit_score": 80, "bullets_to_improve": [], "keywords_to_add": []}
    cv_path, report_path = save_outputs(
        tailored_tex="\\documentclass{article}\n",
        gap_analysis=gap,
        output_dir=tmp_path,
        jd_title="Staff Engineer",
    )
    assert cv_path.exists()
    assert report_path.exists()
    assert cv_path.name.startswith("tailored_cv_staff-engineer_")
    assert cv_path.name.endswith(".tex")
    assert report_path.name.startswith("gap_report_staff-engineer_")
    assert report_path.name.endswith(".md")
    assert cv_path.read_text() == "\\documentclass{article}\n"
    assert "80/100" in report_path.read_text()


def test_save_outputs_does_not_overwrite_previous_run(tmp_path: Path):
    gap = {"fit_score": 50}
    first_cv, first_report = save_outputs(
        "\\tex v1", gap, tmp_path, jd_title="Backend Engineer"
    )
    second_cv, second_report = save_outputs(
        "\\tex v2", gap, tmp_path, jd_title="Backend Engineer"
    )
    assert first_cv != second_cv
    assert first_report != second_report
    assert first_cv.exists() and second_cv.exists()
    assert first_cv.read_text() == "\\tex v1"
    assert second_cv.read_text() == "\\tex v2"


def test_save_outputs_without_jd_title(tmp_path: Path):
    cv_path, report_path = save_outputs("\\tex", {"fit_score": 1}, tmp_path)
    # Bare timestamp suffix — no slug segment
    assert cv_path.name.startswith("tailored_cv_")
    assert report_path.name.startswith("gap_report_")


def test_save_outputs_creates_output_dir(tmp_path: Path):
    target = tmp_path / "deep" / "nested" / "out"
    cv_path, _ = save_outputs("\\tex", {}, target, jd_title="role")
    assert target.is_dir()
    assert cv_path.parent == target


def test_format_report_with_summary_update():
    gap = {
        "fit_score": 65,
        "summary_update_needed": True,
        "summary_suggestion": "Cloud-native backend engineer.",
    }
    out = _format_report(gap)
    assert "Summary Updated" in out
    assert "Cloud-native backend engineer." in out


def test_format_report_minimal_gap():
    out = _format_report({})
    assert "# CV Tailoring Report" in out
    assert "N/A" in out
    # None of the optional sections should appear
    assert "Strong Matches" not in out
    assert "Changes Made" not in out
    assert "Keywords Added" not in out
    assert "Summary Updated" not in out
