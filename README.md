# cv2jd-tailor

Tailor your LaTeX CV to any job description — works with any LLM provider (Claude, GPT, Gemini, Ollama, etc.) via CLI or MCP server.

## Quick Start

### Option A — Python CLI (recommended)
```bash
pip install cv2jd-tailor

cv2jd-tailor tailor cv.tex https://jobs.example.com/123 --model claude-sonnet-4-20250514
cv2jd-tailor tailor cv.tex https://jobs.example.com/123 --model gpt-4o
cv2jd-tailor tailor cv.tex https://jobs.example.com/123 --model ollama/llama3
```

### Option B — Claude Code (zero dependencies)
```bash
cd cv2jd-tailor
claude
> Tailor my CV at ./my_cv.tex for this job: https://jobs.example.com/123
```

### Option C — Convenience script
```bash
./tailor.sh path/to/my_cv.tex https://careers.example.com/job/123
```

## How it works

cv2jd-tailor runs a 6-step pipeline:

1. **Read CV** — parse your LaTeX CV into sections and bullets
2. **Fetch JD** — retrieve the job posting and extract requirements
3. **Gap Analysis** — score fit and identify bullets to improve
4. **Rewrite** — targeted bullet rewrites mirroring JD vocabulary
5. **Validate** — ensure LaTeX integrity (matching braces, no broken commands)
6. **Save & Report** — output tailored CV and a gap report

## Outputs

| File | Description |
|------|-------------|
| `output/tailored_cv.tex` | Your tailored CV — same LaTeX format as the original |
| `output/gap_report.md`   | Fit score, what changed, keywords added, what was left alone |

## MCP Server

Expose cv2jd-tailor as an MCP tool for Claude Desktop, Cursor, or any MCP-compatible client:

```json
{
  "mcpServers": {
    "cv2jd-tailor": {
      "command": "cv2jd-tailor",
      "args": ["mcp"],
      "env": { "CV2JD_MODEL": "claude-sonnet-4-20250514" }
    }
  }
}
```

## Claude Code Setup

If you prefer using Claude Code directly (no Python needed):

1. Install Claude Code: `npm install -g @anthropic-ai/claude-code`
2. Log in: `claude login`
3. Run from this folder — `CLAUDE.md` provides the instructions automatically

## Supported Models

Any model supported by [LiteLLM](https://docs.litellm.ai/docs/providers) works. Examples:

| Provider | Model string |
|----------|-------------|
| Anthropic | `claude-sonnet-4-20250514`, `claude-haiku-4-5-20251001` |
| OpenAI | `gpt-4o`, `gpt-4o-mini` |
| Google | `gemini/gemini-2.5-pro` |
| Ollama (local) | `ollama/llama3`, `ollama/mistral` |
| AWS Bedrock | `bedrock/anthropic.claude-sonnet-4-20250514-v1:0` |
| Azure | `azure/gpt-4o` |

Set via `--model` flag or `CV2JD_MODEL` environment variable.

## Hard Rules

- Never invents experience or skills not in your original CV
- Never changes the LaTeX template structure
- Never adds or removes sections
- Preserves your voice — just sharpens it for the role

## Development

```bash
git clone https://github.com/your-username/cv2jd-tailor.git
cd cv2jd-tailor
pip install -e ".[dev]"
pytest
```

## Contributing

Contributions welcome! Areas where help is especially appreciated:

- Additional CV format support (Markdown, DOCX)
- Better JD extraction for specific job sites
- Prompt tuning for different LLM providers
- UI (web or desktop)

## License

MIT
