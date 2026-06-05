from __future__ import annotations

import json

from patchcontext.cli import main
from patchcontext.pack import to_json, to_markdown
from patchcontext.ranker import rank_files


def test_issue_ranking_selects_file_with_task_terms(tmp_path):
    repo = tmp_path / "repo"
    (repo / "src" / "app").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "src" / "app" / "sessions.py").write_text(
        "class SessionStore:\n"
        "    def expire_stale_sessions(self):\n"
        "        return self._delete_expired()\n",
        encoding="utf-8",
    )
    (repo / "src" / "app" / "users.py").write_text("def create_user():\n    pass\n", encoding="utf-8")
    (repo / "tests" / "test_sessions.py").write_text(
        "from src.app.sessions import SessionStore\n", encoding="utf-8"
    )

    issue = "SessionStore does not expire stale sessions. Failure is in tests/test_sessions.py."

    ranked = rank_files(repo, issue_text=issue, top=3)

    assert any(item.path == "src/app/sessions.py" for item in ranked)
    assert any(item.path == "tests/test_sessions.py" for item in ranked)


def test_failure_trace_is_strong_signal(tmp_path):
    repo = tmp_path / "repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "loader.py").write_text("def load_config():\n    raise ValueError\n", encoding="utf-8")
    (repo / "pkg" / "other.py").write_text("def unrelated():\n    pass\n", encoding="utf-8")
    failure = 'Traceback\n  File "pkg/loader.py", line 3, in load_config\nValueError: bad config\n'

    ranked = rank_files(repo, failure_text=failure, top=1)

    assert ranked[0].path == "pkg/loader.py"
    assert "appears in stack trace" in ranked[0].reasons


def test_pack_outputs_are_stable(tmp_path):
    repo = tmp_path / "repo"
    (repo / "lib").mkdir(parents=True)
    (repo / "lib" / "cache.py").write_text("class CachePolicy:\n    pass\n", encoding="utf-8")
    ranked = rank_files(repo, issue_text="CachePolicy keeps expired entries", top=1)

    assert "| `lib/cache.py` |" in to_markdown(ranked)
    payload = json.loads(to_json(ranked))
    assert payload[0]["path"] == "lib/cache.py"


def test_cli_scan_writes_json(tmp_path):
    repo = tmp_path / "repo"
    (repo / "core").mkdir(parents=True)
    (repo / "core" / "router.py").write_text("def route_request():\n    pass\n", encoding="utf-8")
    issue = tmp_path / "issue.md"
    output = tmp_path / "pack.json"
    issue.write_text("route_request sends API requests to the wrong route", encoding="utf-8")

    exit_code = main(["scan", "--repo", str(repo), "--issue", str(issue), "--format", "json", "-o", str(output)])

    assert exit_code == 0
    assert json.loads(output.read_text(encoding="utf-8"))[0]["path"] == "core/router.py"
