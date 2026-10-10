"""tests/test_diagnostic_tester.py — Test suite for Diagnostic Assessment Engine."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path
import pytest
import tomli_w

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "_tc" / "scripts" / "diagnostic_tester.py"
SKILL_PATH = Path(__file__).resolve().parent.parent / "skills" / "tc-test-me" / "SKILL.md"


@pytest.fixture
def temp_course_tree(tmp_path: Path) -> Path:
    """Create a temporary course tree with mixed section statuses."""
    course_dir = tmp_path / "courses" / "async-python"
    course_dir.mkdir(parents=True)

    manifest_data = {
        "course": {
            "title": "Async Python Mastery",
            "slug": "async-python",
            "version": "1.0.0",
            "status": "in-progress",
            "archetype": "systems",
        },
        "chapter": [
            {
                "title": "Event Loop Internals",
                "slug": "01-event-loop",
                "status": "in-progress",
                "section": [
                    {
                        "title": "Coroutines and Tasks",
                        "slug": "01-coroutines",
                        "status": "completed",
                    },
                    {
                        "title": "Task Cancellation and Timeouts",
                        "slug": "02-cancellation",
                        "status": "review",
                    },
                    {
                        "title": "Custom Event Loops and Selectors",
                        "slug": "03-custom-loops",
                        "status": "not-started",
                    },
                ],
            }
        ],
    }

    with open(course_dir / "course.toml", "wb") as f:
        tomli_w.dump(manifest_data, f)

    # Create notes.md for completed/review sections
    sec1_dir = course_dir / "chapters" / "01-event-loop" / "01-coroutines"
    sec1_dir.mkdir(parents=True)
    (sec1_dir / "notes.md").write_text(
        "# Coroutines\n\n### 3-Bullet Recap\n- A coroutine is a state machine.\n- Tasks wrap coroutines.\n- Event loops drive tasks.\n",
        encoding="utf-8",
    )

    sec2_dir = course_dir / "chapters" / "01-event-loop" / "02-cancellation"
    sec2_dir.mkdir(parents=True)
    (sec2_dir / "notes.md").write_text(
        "# Cancellation\n\n### 3-Bullet Recap\n- Cancel raises CancelledError.\n- Timeout contexts handle deadlines.\n- Shield prevents outer cancellation.\n",
        encoding="utf-8",
    )

    return course_dir


def test_prepare_cumulative_boundary_enforcement(temp_course_tree: Path) -> None:
    """Verify prepare only includes review/completed sections and excludes not-started sections."""
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "prepare",
        "--course",
        str(temp_course_tree),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["eligible_sections_count"] == 2
    assert data["excluded_sections_count"] == 1

    eligible_slugs = [s["section_slug"] for s in data["eligible_sections"]]
    assert "01-coroutines" in eligible_slugs
    assert "02-cancellation" in eligible_slugs
    assert "03-custom-loops" not in eligible_slugs  # Strictly excluded by Cumulative Boundary Rule!

    # Active test section should be the one in 'review'
    assert data["active_test_section"]["section_slug"] == "02-cancellation"
    assert "Cancel raises CancelledError" in data["active_test_section"]["notes_summary"]


def test_prepare_no_eligible_sections(tmp_path: Path) -> None:
    """Verify prepare errors if no sections are in review or completed."""
    course_dir = tmp_path / "courses" / "fresh-course"
    course_dir.mkdir(parents=True)

    manifest_data = {
        "course": {"title": "Fresh Course", "slug": "fresh-course"},
        "chapter": [
            {
                "title": "Ch 1",
                "slug": "01-ch",
                "section": [
                    {"title": "Sec 1", "slug": "01-sec", "status": "not-started"},
                ],
            }
        ],
    }
    with open(course_dir / "course.toml", "wb") as f:
        tomli_w.dump(manifest_data, f)

    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "prepare",
        "--course",
        str(course_dir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 1

    err_data = json.loads(res.stderr)
    assert err_data["ok"] is False
    assert "No sections are eligible for testing" in err_data["error"]


def test_record_cumulative_boundary_violation(temp_course_tree: Path) -> None:
    """Attempting to test a not-started section must fail with Cumulative Boundary Violation."""
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "record",
        "--course",
        str(temp_course_tree),
        "--chapter",
        "01-event-loop",
        "--section",
        "03-custom-loops",  # status is not-started!
        "--prompt",
        "Explain selector mechanics",
        "--response",
        "Epoll based",
        "--outcome",
        "pass",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 1

    err_data = json.loads(res.stderr)
    assert err_data["ok"] is False
    assert "Cumulative Boundary Violation" in err_data["error"]


def test_record_pass_updates_section_status_and_ledger(temp_course_tree: Path) -> None:
    """Passing a review section updates course.toml status to completed and appends to ledger."""
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "record",
        "--course",
        str(temp_course_tree),
        "--chapter",
        "01-event-loop",
        "--section",
        "02-cancellation",
        "--type",
        "hinge_scenario",
        "--prompt",
        "What happens when cancel() is invoked inside a shielded coroutine?",
        "--response",
        "The outer task receives CancelledError while the shielded coroutine runs to completion.",
        "--outcome",
        "pass",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["outcome"] == "pass"
    assert data["section_status_updated"] is True
    assert data["new_section_status"] == "completed"

    # Verify ledger file
    ledger_path = temp_course_tree / "test-ledger.jsonl"
    assert ledger_path.is_file()
    lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["section"] == "02-cancellation"
    assert record["outcome"] == "pass"
    assert record["diagnosed_misconception"] == "NONE"

    # Verify course.toml was atomically updated
    with open(temp_course_tree / "course.toml", "rb") as f:
        updated_manifest = tomllib.load(f)
    sec2 = updated_manifest["chapter"][0]["section"][1]
    assert sec2["status"] == "completed"


def test_record_fail_appends_misconception_and_keeps_review_status(temp_course_tree: Path) -> None:
    """Failing a section logs the diagnosed misconception and keeps status as review."""
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "record",
        "--course",
        str(temp_course_tree),
        "--chapter",
        "01-event-loop",
        "--section",
        "02-cancellation",
        "--type",
        "hinge_scenario",
        "--prompt",
        "What happens when cancel() is called?",
        "--response",
        "The thread is terminated immediately.",
        "--outcome",
        "fail",
        "--misconception",
        "CONFUSION_THREAD_VS_COROUTINE_CANCELLATION",
        "--remediation",
        "Coroutines operate on a single thread and cancel() injects CancelledError at await points.",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["outcome"] == "fail"
    assert data["section_status_updated"] is False
    assert data["new_section_status"] == "review"

    # Verify ledger file
    ledger_path = temp_course_tree / "test-ledger.jsonl"
    lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    record = json.loads(lines[0])
    assert record["outcome"] == "fail"
    assert record["diagnosed_misconception"] == "CONFUSION_THREAD_VS_COROUTINE_CANCELLATION"

    # Verify course.toml was not changed to completed
    with open(temp_course_tree / "course.toml", "rb") as f:
        manifest = tomllib.load(f)
    assert manifest["chapter"][0]["section"][1]["status"] == "review"


def test_zero_bmad_references() -> None:
    """Verify strict absence of BMad leakage in diagnostic tester script and skill."""
    forbidden = ["bmad", "b-mad", "b_mad", "BMAD", "Bmad"]
    script_content = SCRIPT_PATH.read_text(encoding="utf-8")
    skill_content = SKILL_PATH.read_text(encoding="utf-8")

    for word in forbidden:
        assert word not in script_content, f"Found '{word}' in {SCRIPT_PATH}"
        assert word not in skill_content, f"Found '{word}' in {SKILL_PATH}"
