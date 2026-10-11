"""tests/test_tc_dispatcher.py — Unit tests for TextCourses unified CLI dispatcher (tc.py).

Verifies:
1. Top-level usage help and version reporting.
2. Routing to individual engine modules (init, teach, notes, test, etc.).
3. Standard JSON error reporting on invalid commands.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TC_DISPATCHER = Path(__file__).resolve().parent.parent / "_tc" / "scripts" / "tc.py"


def test_tc_dispatcher_help():
    """Verify top-level tc.py displays usage and lists all core subcommands."""
    res = subprocess.run(
        [sys.executable, str(TC_DISPATCHER), "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "TextCourses Unified Dispatcher (tc)" in res.stdout
    for cmd in ["init", "research", "create", "teach", "practicals", "test", "notes", "audit", "dag", "memlog", "hash"]:
        assert cmd in res.stdout


def test_tc_dispatcher_version():
    """Verify tc.py reports engine version."""
    res = subprocess.run(
        [sys.executable, str(TC_DISPATCHER), "--version"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "TextCourses Engine v" in res.stdout


def test_tc_dispatcher_subcommand_forwarding():
    """Verify tc.py correctly forwards arguments to submodules."""
    # Test forwarding to teach
    res_teach = subprocess.run(
        [sys.executable, str(TC_DISPATCHER), "teach", "--help"],
        capture_output=True,
        text=True,
    )
    assert res_teach.returncode == 0
    assert "session" in res_teach.stdout
    assert "advance" in res_teach.stdout

    # Test forwarding to notes
    res_notes = subprocess.run(
        [sys.executable, str(TC_DISPATCHER), "notes", "--help"],
        capture_output=True,
        text=True,
    )
    assert res_notes.returncode == 0
    assert "compile" in res_notes.stdout
    assert "audit-readability" in res_notes.stdout


def test_tc_dispatcher_unknown_subcommand_json():
    """Verify tc.py returns structured JSON error on unknown subcommand."""
    res = subprocess.run(
        [sys.executable, str(TC_DISPATCHER), "nonexistent-command", "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode != 0
    data = json.loads(res.stdout)
    assert data["ok"] is False
    assert "Unknown subcommand" in data["error"]
