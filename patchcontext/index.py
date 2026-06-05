from __future__ import annotations

import ast
import re
from pathlib import Path

from .models import FileRecord

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "target",
    "__pycache__",
}
TEXT_SUFFIXES = {
    ".py",
    ".pyi",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".md",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
}
IMPORT_RE = re.compile(r"""(?:from|import)\s+["'](\.{1,2}/[^"']+)["']""")


def build_index(repo: str | Path, max_file_bytes: int = 200_000) -> list[FileRecord]:
    root = Path(repo).resolve()
    records: list[FileRecord] = []
    for path in _iter_text_files(root):
        text = _read_limited(path, max_file_bytes)
        rel = path.relative_to(root).as_posix()
        records.append(FileRecord(path=rel, text=text, imports=_extract_imports(root, path, text)))
    return records


def _iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        parts = set(path.relative_to(root).parts)
        if parts & EXCLUDED_DIRS:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        yield path


def _read_limited(path: Path, max_bytes: int) -> str:
    data = path.read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="replace")


def _extract_imports(root: Path, path: Path, text: str) -> set[str]:
    if path.suffix == ".py":
        return _extract_python_imports(root, path, text)
    if path.suffix in {".js", ".jsx", ".ts", ".tsx"}:
        return _extract_js_imports(root, path, text)
    return set()


def _extract_python_imports(root: Path, path: Path, text: str) -> set[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.update(_module_to_paths(root, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.update(_module_to_paths(root, node.module))
    return imported


def _module_to_paths(root: Path, module: str) -> set[str]:
    rel = module.replace(".", "/")
    paths = {f"{rel}.py", f"{rel}/__init__.py"}
    return {path for path in paths if (root / path).exists()}


def _extract_js_imports(root: Path, path: Path, text: str) -> set[str]:
    found: set[str] = set()
    for match in IMPORT_RE.finditer(text):
        target = match.group(1)
        resolved = (path.parent / target).resolve()
        for suffix in ("", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.js"):
            candidate = Path(f"{resolved}{suffix}")
            if candidate.exists() and root in candidate.parents:
                found.add(candidate.relative_to(root).as_posix())
                break
    return found

