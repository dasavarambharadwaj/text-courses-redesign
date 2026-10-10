"""tests/test_lesson_tracker.py — Comprehensive test suite for session hygiene and lesson plan tracker."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

TRACKER_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "lesson_tracker.py"


def test_tracker_cli_help():
    """Verify lesson_tracker CLI prints help message and exits 0."""
    res = subprocess.run([sys.executable, str(TRACKER_SCRIPT), "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "status" in res.stdout
    assert "current" in res.stdout
    assert "tick" in res.stdout


def test_tracker_pep_723_metadata():
    """Verify script contains valid PEP 723 metadata header."""
    content = TRACKER_SCRIPT.read_text(encoding="utf-8")
    assert "# /// script" in content
    assert 'requires-python = ">=3.11"' in content
    assert "tomli-w>=" in content
    assert "# ///" in content


def test_zero_bmad_references():
    """Verify strict zero-BMad references in scripts and test suite."""
    text = TRACKER_SCRIPT.read_text(encoding="utf-8")
    assert not re.search(r"\bbmad\b", text, re.IGNORECASE), f"Found BMad mention in {TRACKER_SCRIPT}"


def test_status_inspection(tmp_path: Path):
    """Verify status reports total, completed, remaining, and percentage correctly."""
    plan_file = tmp_path / "lesson-plan.md"
    plan_file.write_text(
        "# Lesson Plan: Tokio Tasks\n\n"
        "## Concepts\n"
        "- [x] Task spawning mechanics\n"
        "- [ ] JoinHandle awaiting\n"
        "- [ ] Cooperative cancellation tokens\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, str(TRACKER_SCRIPT), "status", "--path", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["total_items"] == 3
    assert data["completed_items"] == 1
    assert data["remaining_items"] == 2
    assert data["percent_complete"] == 33.3
    assert data["all_completed"] is False


def test_current_concept_and_interruption_recovery(tmp_path: Path):
    """Verify current returns the exact first uncompleted concept for session recovery."""
    plan_file = tmp_path / "lesson-plan.md"
    plan_file.write_text(
        "# Lesson Plan: Concurrency\n\n"
        "## Checklist\n"
        "- [x] Mutex primitives\n"
        "- [ ] Condition variables signaling\n"
        "- [ ] Read-write locks\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, str(TRACKER_SCRIPT), "current", "--path", str(plan_file), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["has_active_concept"] is True
    assert data["index"] == 1
    assert data["concept"] == "Condition variables signaling"
    assert data["remaining_items"] == 2


def test_tick_concept_atomically_updates_disk(tmp_path: Path):
    """Verify tick updates markdown checkmark atomically while preserving rest of file."""
    plan_file = tmp_path / "lesson-plan.md"
    initial_text = (
        "# Lesson Plan: Raft\n\n"
        "> Internal AI Teacher Guide\n\n"
        "## Concepts\n"
        "- [ ] Leader election term numbers\n"
        "- [ ] Heartbeat timers\n"
    )
    plan_file.write_text(initial_text, encoding="utf-8")

    # 1. Tick first item
    res1 = subprocess.run(
        [sys.executable, str(TRACKER_SCRIPT), "tick", "--path", str(plan_file), "--json"],
        capture_output=True,
        text=True,
    )
    assert res1.returncode == 0
    d1 = json.loads(res1.stdout)
    assert d1["ticked_index"] == 0
    assert d1["remaining_items"] == 1
    assert d1["section_fully_completed"] is False

    updated_text_1 = plan_file.read_text(encoding="utf-8")
    assert "- [x] Leader election term numbers" in updated_text_1
    assert "- [ ] Heartbeat timers" in updated_text_1
    assert "> Internal AI Teacher Guide" in updated_text_1

    # 2. Tick second item by concept name
    res2 = subprocess.run(
        [
            sys.executable,
            str(TRACKER_SCRIPT),
            "tick",
            "--path",
            str(plan_file),
            "--concept",
            "Heartbeat timers",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res2.returncode == 0
    d2 = json.loads(res2.stdout)
    assert d2["ticked_index"] == 1
    assert d2["remaining_items"] == 0
    assert d2["section_fully_completed"] is True

    # Check current on fully completed plan
    res_curr = subprocess.run(
        [sys.executable, str(TRACKER_SCRIPT), "current", "--path", str(plan_file), "--json"],
        capture_output=True,
        text=True,
    )
    assert res_curr.returncode == 0
    d_curr = json.loads(res_curr.stdout)
    assert d_curr["has_active_concept"] is False
    assert d_curr["remaining_items"] == 0


def test_tick_out_of_bounds_index_fails(tmp_path: Path):
    """Verify tick with invalid index returns error and exits 1."""
    plan_file = tmp_path / "lesson-plan.md"
    plan_file.write_text("- [ ] Solo concept\n", encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(TRACKER_SCRIPT), "tick", "--path", str(plan_file), "--index", "99", "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    err_data = json.loads(res.stderr)
    assert "error" in err_data
