"""LaTeX parsing and validation utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class CVSection:
    """A section extracted from a LaTeX CV."""

    name: str
    raw: str
    bullets: list[str] = field(default_factory=list)


@dataclass
class ParsedCV:
    """Structured representation of a LaTeX CV."""

    preamble: str
    sections: list[CVSection]
    raw: str


# LaTeX special characters that must be escaped
SPECIAL_CHARS = set("&%$#_{}~^")

# Pattern to match \section or \subsection commands
SECTION_RE = re.compile(
    r"\\(section|subsection)\*?\s*\{([^}]*)\}",
    re.MULTILINE,
)

# Pattern to match \item or \cvitem-style bullets
BULLET_RE = re.compile(
    r"\\(?:item|cvitem|cventry|cvlistitem)\s*(?:\[[^\]]*\])?\s*\{?",
    re.MULTILINE,
)


def parse_cv(tex: str) -> ParsedCV:
    """Parse a LaTeX CV into preamble and sections."""
    # Split at \begin{document}
    parts = tex.split(r"\begin{document}", maxsplit=1)
    if len(parts) == 2:
        preamble = parts[0] + r"\begin{document}"
        body = parts[1]
    else:
        preamble = ""
        body = tex

    sections = _extract_sections(body)
    return ParsedCV(preamble=preamble, sections=sections, raw=tex)


def _extract_sections(body: str) -> list[CVSection]:
    """Extract sections and their bullets from the document body."""
    matches = list(SECTION_RE.finditer(body))
    if not matches:
        # No sections found — treat the whole body as one section
        bullets = _extract_bullets(body)
        return [CVSection(name="(body)", raw=body, bullets=bullets)]

    sections: list[CVSection] = []

    # Text before first section
    pre = body[: matches[0].start()].strip()
    if pre:
        sections.append(
            CVSection(name="(header)", raw=pre, bullets=_extract_bullets(pre))
        )

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        raw = body[start:end]
        name = match.group(2).strip()
        bullets = _extract_bullets(raw)
        sections.append(CVSection(name=name, raw=raw, bullets=bullets))

    return sections


def _extract_bullets(text: str) -> list[str]:
    """Extract bullet-point content from a section."""
    bullets: list[str] = []
    matches = list(BULLET_RE.finditer(text))
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        # Clean up trailing braces/commands
        content = re.sub(r"\s*\\(?:end\{|\\)", "", content).strip()
        if content:
            bullets.append(content)
    return bullets


@dataclass
class ValidationIssue:
    """A single LaTeX validation issue."""

    line: int
    message: str
    severity: str = "error"  # "error" or "warning"


def validate_latex(tex: str) -> list[ValidationIssue]:
    """Validate LaTeX source for common issues."""
    issues: list[ValidationIssue] = []
    issues.extend(_check_matching_environments(tex))
    issues.extend(_check_matching_braces(tex))
    issues.extend(_check_unescaped_special_chars(tex))
    return issues


def _check_matching_environments(tex: str) -> list[ValidationIssue]:
    """Check that all \\begin{} have matching \\end{}."""
    issues: list[ValidationIssue] = []
    stack: list[tuple[str, int]] = []
    env_re = re.compile(r"\\(begin|end)\{(\w+)\}")

    for i, line in enumerate(tex.splitlines(), start=1):
        for match in env_re.finditer(line):
            cmd, env = match.group(1), match.group(2)
            if cmd == "begin":
                stack.append((env, i))
            elif cmd == "end":
                if not stack:
                    issues.append(
                        ValidationIssue(i, f"\\end{{{env}}} without matching \\begin")
                    )
                else:
                    expected_env, begin_line = stack.pop()
                    if expected_env != env:
                        issues.append(
                            ValidationIssue(
                                i,
                                f"\\end{{{env}}} does not match "
                                f"\\begin{{{expected_env}}} at line {begin_line}",
                            )
                        )

    for env, line in stack:
        issues.append(ValidationIssue(line, f"\\begin{{{env}}} never closed"))

    return issues


def _check_matching_braces(tex: str) -> list[ValidationIssue]:
    """Check that curly braces are balanced."""
    issues: list[ValidationIssue] = []
    depth = 0
    for i, line in enumerate(tex.splitlines(), start=1):
        for ch in line:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth < 0:
                    issues.append(ValidationIssue(i, "Unmatched closing brace '}'"))
                    depth = 0

    if depth > 0:
        issues.append(
            ValidationIssue(0, f"{depth} unclosed opening brace(s) in document")
        )

    return issues


def _check_unescaped_special_chars(tex: str) -> list[ValidationIssue]:
    """Check for unescaped special LaTeX characters in text content."""
    issues: list[ValidationIssue] = []
    # Only check outside of commands — look for bare & % $ # _ not preceded by \
    # Skip lines that are comments or commands
    for i, line in enumerate(tex.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("%"):
            continue
        # Check for unescaped & outside of tabular-like environments
        # We check for bare & not preceded by backslash
        for match in re.finditer(r"(?<!\\)&", line):
            # Allow & in tabular/align environments (heuristic: skip if line has \\)
            if "\\\\" not in line:
                issues.append(
                    ValidationIssue(
                        i, "Possibly unescaped '&'", severity="warning"
                    )
                )
                break

    return issues
