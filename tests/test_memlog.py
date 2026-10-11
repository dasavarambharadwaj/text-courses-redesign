"""test_memlog.py — Automated test suite for _tc/scripts/memlog.py.

Verifies initialization, chronological append operations, frontmatter mutation,
tail extraction for context injection, and atomic persistence (FR-28).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "_tc" / "scripts" / "memlog.py"


def run_memlog(*args: str) -> tuple[int, dict]:
    """Execute memlog.py with arguments and return (exit_code, parsed_json)."""
    cmd = [sys.executable, str(SCRIPT_PATH), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout.strip() or proc.stderr.strip()
    try:
        data = json.loads(out)
    except Exception:
        data = {"raw": out}
    return proc.returncode, data


def test_memlog_init(tmp_path: Path) -> None:
    """Test initializing a pedagogical memlog with frontmatter."""
    memlog_file = tmp_path / "memlog.md"
    code, res = run_memlog(
        "init",
        "--path", str(memlog_file),
        "--topic", "Distributed Systems Track",
        "--teacher", "Feynman",
        "--goal", "Master Raft consensus",
    )
    assert code == 0
    assert res["ok"] is True
    assert memlog_file.exists()

    content = memlog_file.read_text(encoding="utf-8")
    assert 'topic: "Distributed Systems Track"' in content or "Distributed Systems Track" in content
    assert "Feynman" in content
    assert "Master Raft consensus" in content


def test_memlog_append_with_tags(tmp_path: Path) -> None:
    """Test appending structured pedagogical entries."""
    memlog_file = tmp_path / "memlog.md"
    run_memlog("init", "--path", str(memlog_file), "--topic", "Python Mechanics")

    # Append concept
    code, res = run_memlog(
        "append",
        "--path", str(memlog_file),
        "--type", "concept",
        "--by", "Feynman",
        "--text", "Taught NumPy strided buffer layout",
    )
    assert code == 0
    assert res["ok"] is True

    # Append question
    code, _ = run_memlog(
        "append",
        "--path", str(memlog_file),
        "--type", "question",
        "--by", "learner",
        "--text", "Does transpose create a copy in RAM?",
    )
    assert code == 0

    # Append handoff
    code, _ = run_memlog(
        "append",
        "--path", str(memlog_file),
        "--type", "handoff",
        "--text", "Feynman handed off to Euclid for axiomatic matrix proof",
    )
    assert code == 0

    content = memlog_file.read_text(encoding="utf-8")
    assert "- (concept by Feynman) Taught NumPy strided buffer layout" in content
    assert "- (question by learner) Does transpose create a copy in RAM?" in content
    assert "- (handoff) Feynman handed off to Euclid for axiomatic matrix proof" in content


def test_memlog_set_frontmatter(tmp_path: Path) -> None:
    """Test updating frontmatter fields atomically."""
    memlog_file = tmp_path / "memlog.md"
    run_memlog("init", "--path", str(memlog_file), "--topic", "AI Apprenticeship")

    code, res = run_memlog("set", "--path", str(memlog_file), "--key", "active_course", "--value", "linear-algebra")
    assert code == 0
    assert res["ok"] is True

    content = memlog_file.read_text(encoding="utf-8")
    assert "active_course: linear-algebra" in content


def test_memlog_tail_context_injection(tmp_path: Path) -> None:
    """Test tail command extracting last N entries for turn context."""
    memlog_file = tmp_path / "memlog.md"
    run_memlog("init", "--path", str(memlog_file))

    for i in range(20):
        run_memlog("append", "--path", str(memlog_file), "--text", f"Entry milestone {i}")

    code, res = run_memlog("tail", "--path", str(memlog_file), "--n", "5")
    assert code == 0
    assert res["ok"] is True
    assert res["count"] == 5
    assert res["total_entries"] == 20
    assert res["entries"][-1] == "- Entry milestone 19"


def test_memlog_inspect(tmp_path: Path) -> None:
    """Test inspect command returning full parsed log."""
    memlog_file = tmp_path / "memlog.md"
    run_memlog("init", "--path", str(memlog_file), "--topic", "Compilers")
    run_memlog("append", "--path", str(memlog_file), "--type", "concept", "--text", "AST lowering")

    code, res = run_memlog("inspect", "--path", str(memlog_file))
    assert code == 0
    assert res["ok"] is True
    assert res["frontmatter"]["topic"] == "Compilers"
    assert len(res["entries"]) == 1
