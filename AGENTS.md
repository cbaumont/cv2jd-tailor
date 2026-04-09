# Development Instructions for cv2jd-tailor

**Architecture:** Python package with LiteLLM backend, CLI, MCP server. Original Claude Code workflow preserved in `claude-code/`.

**Code Style:**
- Use type hints
- LaTeX utilities are pure Python, no LLM calls
- LLM-powered steps: gap_analysis, rewrite; others are deterministic
- Test deterministic code; mock LLM calls

**Testing:**
- Run `pytest` before committing
- Add tests for new logic
- Fixtures in `tests/fixtures/`

**Commits:**
- One commit per logical change
- Message format: `Short description of changes` (e.g., `Add feature X`, `Fix bug Y`)
- Include `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>` footer

**Key Files:**
- `src/cv2jd_tailor/latex_utils.py` — LaTeX parsing and validation
- `src/cv2jd_tailor/steps/` — pipeline steps
- `src/cv2jd_tailor/llm/` — LLM backend abstraction
- `src/cv2jd_tailor/cli.py` — CLI entry point
- `src/cv2jd_tailor/mcp_server.py` — MCP server

**Hard Rule:** Do NOT add comments to code.
