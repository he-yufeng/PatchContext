# PatchContext

[中文文档 / Chinese README](README_CN.md)

Give coding agents the files that matter for one issue, one failing test, or one patch.

PatchContext builds a small, explainable context pack from task evidence. It looks at issue
text, stack traces, failure logs, git diffs, file names, content terms, and light Python/JS/TS
import links, then ranks the files a coding agent should read first.

It is not a whole-repo packer and it is not a project documentation generator. Use Repomix
when you want to hand over the whole repository. Use RepoWiki when you want durable project
docs. Use PatchContext when the task is narrower: "fix this issue" or "debug this CI failure".

## Quick Start

```bash
pip install patchcontext
patchcontext scan --repo . --issue issue.md --top 12 > context.md
```

From a failing log:

```bash
pytest -q 2>&1 | tee pytest.log
patchcontext from-failure --repo . pytest.log --format md
```

From the current diff:

```bash
patchcontext from-diff --repo . --base main --format json
```

## What The Pack Looks Like

```markdown
# PatchContext Pack

| Rank | File | Score | Why selected |
|---:|---|---:|---|
| 1 | `src/app/sessions.py` | 72.50 | mentioned directly; content matches task terms |
| 2 | `tests/test_sessions.py` | 45.00 | mentioned directly |
```

Each selected file includes a score and a short reason. The reasons matter: a task pack that
cannot explain why a file was selected is just another black box.

## Why This Exists

AI coding agents often fail because the context is noisy, not because the repository is too
small. A whole-repo dump can bury the five files that actually matter under hundreds of
unrelated files. PatchContext keeps the first pass focused:

- extract paths from issue text, stack traces, and diffs;
- rank files by path and content signals;
- add light import-neighbor context for Python and JS/TS;
- output a Markdown or JSON artifact that can be pasted into Codex, Claude Code, ChatGPT, or
  a PR debugging note.

## Commands

```bash
patchcontext scan --repo . --issue issue.md --failure pytest.log
patchcontext from-failure --repo . pytest.log
patchcontext from-diff --repo . --base main
```

Common options:

- `--top 20`: include more files.
- `--max-file-bytes 100000`: skip huge generated or vendored files while indexing.
- `--format json`: machine-readable output.
- `--output context.md`: write to a file.

## Design Boundaries

PatchContext deliberately stays small:

- no live LLM calls;
- no hidden telemetry;
- no full LSP server;
- no attempt to summarize or rewrite your code;
- no claim that the ranking is perfect.

The first pass should be cheap, deterministic, and easy to inspect.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
python -m build
```

## License

MIT
