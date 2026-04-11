"""CLI smoke tests via typer's CliRunner."""

from pathlib import Path

from typer.testing import CliRunner

from cv2jd_tailor import cli as cli_module
from cv2jd_tailor.cli import app
from cv2jd_tailor.pipeline import PipelineResult
from cv2jd_tailor.latex_utils import parse_cv

FIXTURES = Path(__file__).parent / "fixtures"

runner = CliRunner()


def test_tailor_requires_model(monkeypatch, tmp_path):
    # Ensure no env model sneaks in
    monkeypatch.delenv("CV2JD_MODEL", raising=False)
    result = runner.invoke(app, ["tailor", str(FIXTURES / "sample_cv.tex"), "https://x"])
    assert result.exit_code == 1
    assert "No model specified" in result.output


def test_tailor_reports_results(monkeypatch, tmp_path):
    cv = parse_cv((FIXTURES / "sample_cv.tex").read_text())
    saved_cv = tmp_path / "tailored_cv_role_ts.tex"
    saved_cv.write_text("\\tex")
    saved_report = tmp_path / "gap_report_role_ts.md"
    saved_report.write_text("# report")

    fake_result = PipelineResult(
        cv=cv,
        jd=None,  # type: ignore[arg-type]
        gap_analysis={"fit_score": 88, "bullets_to_improve": [{}, {}]},
        tailored_tex="\\tex",
        is_valid=True,
        validation_issues=[],
        cv_path=saved_cv,
        report_path=saved_report,
    )

    def _fake_run_pipeline(**kwargs):
        assert kwargs["cv_path"] == str(FIXTURES / "sample_cv.tex")
        assert kwargs["output_dir"] == str(tmp_path)
        return fake_result

    # Stop LiteLLMBackend from actually calling out
    monkeypatch.setattr(cli_module, "LiteLLMBackend", lambda **kw: object())
    monkeypatch.setattr(cli_module, "run_pipeline", _fake_run_pipeline)

    result = runner.invoke(
        app,
        [
            "tailor",
            str(FIXTURES / "sample_cv.tex"),
            "https://jobs.example.com/1",
            "--model",
            "mock-model",
            "--output-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Fit score: 88/100" in result.output
    assert "Bullets rewritten: 2" in result.output
    assert "tailored_cv_role_ts.tex" in result.output


def test_tailor_dry_run_prints_gap_json(monkeypatch, tmp_path):
    cv = parse_cv((FIXTURES / "sample_cv.tex").read_text())
    fake_result = PipelineResult(
        cv=cv,
        jd=None,  # type: ignore[arg-type]
        gap_analysis={"fit_score": 60, "bullets_to_improve": []},
        tailored_tex="\\tex",
        is_valid=True,
        validation_issues=[],
    )
    monkeypatch.setattr(cli_module, "LiteLLMBackend", lambda **kw: object())
    monkeypatch.setattr(cli_module, "run_pipeline", lambda **kw: fake_result)

    result = runner.invoke(
        app,
        [
            "tailor",
            str(FIXTURES / "sample_cv.tex"),
            "https://example.com",
            "--model",
            "mock",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Dry run" in result.output
    assert '"fit_score": 60' in result.output


def test_tailor_handles_pipeline_errors(monkeypatch):
    def _boom(**kwargs):
        raise RuntimeError("upstream failure")

    monkeypatch.setattr(cli_module, "LiteLLMBackend", lambda **kw: object())
    monkeypatch.setattr(cli_module, "run_pipeline", _boom)

    result = runner.invoke(
        app,
        [
            "tailor",
            str(FIXTURES / "sample_cv.tex"),
            "https://example.com",
            "--model",
            "mock",
        ],
    )
    assert result.exit_code == 1
    assert "upstream failure" in result.output


def test_validate_missing_file(tmp_path):
    result = runner.invoke(app, ["validate", str(tmp_path / "nope.tex")])
    assert result.exit_code == 1
    assert "File not found" in result.output


def test_validate_clean_fixture():
    result = runner.invoke(app, ["validate", str(FIXTURES / "sample_cv.tex")])
    # sample_cv.tex is known-good
    assert result.exit_code == 0
    assert "No issues found" in result.output


def test_validate_broken_tex_returns_error(tmp_path):
    broken = tmp_path / "broken.tex"
    broken.write_text(
        "\\begin{document}\n\\begin{itemize}\n\\item x\n\\end{document}\n"
    )
    result = runner.invoke(app, ["validate", str(broken)])
    assert result.exit_code == 1
    assert "ERROR" in result.output
