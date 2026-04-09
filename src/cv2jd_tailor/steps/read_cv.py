"""Step 1: Read and parse a LaTeX CV file."""

from __future__ import annotations

from pathlib import Path

from cv2jd_tailor.latex_utils import ParsedCV, parse_cv


def read_cv(cv_path: str | Path) -> ParsedCV:
    """Read a .tex file and parse it into structured sections."""
    path = Path(cv_path)
    if not path.exists():
        raise FileNotFoundError(f"CV file not found: {path}")
    if path.suffix != ".tex":
        raise ValueError(f"Expected a .tex file, got: {path.suffix}")

    tex = path.read_text(encoding="utf-8")
    return parse_cv(tex)
