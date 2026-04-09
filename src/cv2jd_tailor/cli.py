"""CLI entry point for cv2jd-tailor."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from cv2jd_tailor.latex_utils import validate_latex
from cv2jd_tailor.llm.litellm_backend import LiteLLMBackend
from cv2jd_tailor.pipeline import run_pipeline

app = typer.Typer(
    name="cv2jd-tailor",
    help="Tailor your LaTeX CV to any job description.",
    no_args_is_help=True,
)


@app.command()
def tailor(
    cv_path: str = typer.Argument(help="Path to your LaTeX CV (.tex file)"),
    job_url: str = typer.Argument(help="URL of the job posting"),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        envvar="CV2JD_MODEL",
        help="LLM model to use (e.g. claude-sonnet-4-20250514, gpt-4o, ollama/llama3)",
    ),
    output_dir: str = typer.Option("output", "--output-dir", "-o", help="Output directory"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run analysis only, don't save"),
    temperature: float = typer.Option(0.3, "--temperature", "-t", help="LLM temperature"),
) -> None:
    """Tailor a CV for a specific job posting."""
    if model is None:
        typer.echo("Error: No model specified. Use --model or set CV2JD_MODEL env var.")
        raise typer.Exit(1)

    typer.echo(f"cv2jd-tailor v0.1.0")
    typer.echo(f"  CV:    {cv_path}")
    typer.echo(f"  Job:   {job_url}")
    typer.echo(f"  Model: {model}")
    typer.echo()

    llm = LiteLLMBackend(model=model, temperature=temperature)

    try:
        typer.echo("Step 1/6: Reading CV...")
        typer.echo("Step 2/6: Fetching job description...")
        typer.echo("Step 3/6: Running gap analysis...")
        typer.echo("Step 4/6: Rewriting targeted bullets...")
        typer.echo("Step 5/6: Validating LaTeX...")

        result = run_pipeline(
            cv_path=cv_path,
            job_url=job_url,
            llm=llm,
            output_dir=output_dir,
            dry_run=dry_run,
        )

        # Report results
        typer.echo()
        score = result.gap_analysis.get("fit_score", "N/A")
        typer.echo(f"Fit score: {score}/100")

        n_changes = len(result.gap_analysis.get("bullets_to_improve", []))
        typer.echo(f"Bullets rewritten: {n_changes}")

        if not result.is_valid:
            typer.echo(f"Warning: {len(result.validation_issues)} LaTeX issue(s) detected")
            for issue in result.validation_issues:
                typer.echo(f"  Line {issue.line}: {issue.message}")

        if dry_run:
            typer.echo()
            typer.echo("Dry run — gap analysis:")
            typer.echo(json.dumps(result.gap_analysis, indent=2))
        else:
            typer.echo()
            typer.echo(f"Step 6/6: Saved!")
            typer.echo(f"  CV:     {result.cv_path}")
            typer.echo(f"  Report: {result.report_path}")

    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def validate(
    cv_path: str = typer.Argument(help="Path to a LaTeX file to validate"),
) -> None:
    """Validate a LaTeX CV file for common issues."""
    path = Path(cv_path)
    if not path.exists():
        typer.echo(f"Error: File not found: {cv_path}", err=True)
        raise typer.Exit(1)

    tex = path.read_text(encoding="utf-8")
    issues = validate_latex(tex)

    if not issues:
        typer.echo("No issues found.")
        raise typer.Exit(0)

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    for issue in issues:
        prefix = "ERROR" if issue.severity == "error" else "WARN"
        typer.echo(f"  [{prefix}] Line {issue.line}: {issue.message}")

    typer.echo()
    typer.echo(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    raise typer.Exit(1 if errors else 0)


@app.command()
def mcp() -> None:
    """Start the MCP server for use with Claude Desktop, Cursor, etc."""
    from cv2jd_tailor.mcp_server import mcp as mcp_server

    typer.echo("Starting cv2jd-tailor MCP server...")
    mcp_server.run()


if __name__ == "__main__":
    app()
