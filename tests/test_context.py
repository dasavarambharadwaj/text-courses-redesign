"""test_context.py — Unit tests for TextCourses Context Loading Manifest engine (context.py).

Verifies Stage Loading Matrix enforcement, authorized manifest generation per skill,
turn budget constraints (<4,000 tokens), and rejection of out-of-scope or concept-leaking reads (AD-5, FR-22).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

CONTEXT_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "context.py"


def run_context(*args: str) -> subprocess.CompletedProcess[str]:
    """Helper to run context.py CLI and capture stdout/stderr."""
    cmd = [sys.executable, str(CONTEXT_SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_context_help():
    """Verify help subcommand displays usage and available subcommands."""
    result = run_context("--help")
    assert result.returncode == 0
    assert "TextCourses stage-aware Context Loading Manifest engine" in result.stdout
    assert "get-manifest" in result.stdout
    assert "check" in result.stdout
    assert "matrix" in result.stdout


def test_get_manifest_tc_teach_success(tmp_path: Path):
    """Verify tc-teach generates authorized manifest with course.toml, active lesson-plan, notes, and test-ledger."""
    course_dir = tmp_path / "course-rust"
    course_dir.mkdir(parents=True)

    manifest_file = course_dir / "course.toml"
    content = """
[course]
slug = "rust-primer"
title = "Rust Primer"
status = "in_progress"

[[chapters]]
id = 1
slug = "ch-01-basics"
title = "Basics"

[[chapters.sections]]
id = 1
slug = "sec-01-variables"
title = "Variables"
status = "completed"

[[chapters.sections]]
id = 2
slug = "sec-02-ownership"
title = "Ownership"
status = "in_progress"
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    # Create dummy files
    sec1_dir = course_dir / "ch-01-basics" / "sec-01-variables"
    sec1_dir.mkdir(parents=True)
    (sec1_dir / "lesson-plan.md").write_text("# LP 1", encoding="utf-8")
    (sec1_dir / "notes.md").write_text("# Notes 1", encoding="utf-8")

    sec2_dir = course_dir / "ch-01-basics" / "sec-02-ownership"
    sec2_dir.mkdir(parents=True)
    (sec2_dir / "lesson-plan.md").write_text("# LP 2", encoding="utf-8")
    (sec2_dir / "notes.md").write_text("# Notes 2", encoding="utf-8")

    (course_dir / "test-ledger.jsonl").write_text('{"entry": 1}\n', encoding="utf-8")

    result = run_context("get-manifest", "--skill", "tc-teach", "--path", str(course_dir))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["skill"] == "tc-teach"
    assert data["active_section"]["id"] == 2
    assert data["active_section"]["slug"] == "sec-02-ownership"
    assert data["budget_tokens"] <= 4000

    files = data["authorized_files"]
    assert any("course.toml" in f for f in files)
    assert any("sec-02-ownership/lesson-plan.md" in f or "lesson-plan.md" in f for f in files)
    assert any("notes.md" in f for f in files)
    assert any("test-ledger.jsonl" in f for f in files)


def test_get_manifest_tc_teach_missing_active_section(tmp_path: Path):
    """Verify tc-teach exits with code 1 and guidance when no active section is in progress."""
    course_dir = tmp_path / "course-idle"
    course_dir.mkdir(parents=True)

    manifest_file = course_dir / "course.toml"
    content = """
[course]
slug = "idle-course"
title = "Idle Course"
status = "completed"

[[chapters]]
id = 1
slug = "ch-01"
title = "Ch 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Sec 1"
status = "completed"
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_context("get-manifest", "--skill", "tc-teach", "--path", str(course_dir))
    assert result.returncode == 1
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert "No active section found" in err_data["error"]
    assert "guidance" in err_data


def test_get_manifest_tc_test_me_omits_lesson_plans(tmp_path: Path):
    """Verify tc-test-me strictly omits lesson-plan.md to prevent concept leaks (AD-5)."""
    course_dir = tmp_path / "course-testing"
    course_dir.mkdir(parents=True)

    manifest_file = course_dir / "course.toml"
    content = """
[course]
slug = "test-course"
title = "Test Course"
status = "in_progress"

[[chapters]]
id = 1
slug = "ch-01"
title = "Ch 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Sec 1"
status = "completed"
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    sec1_dir = course_dir / "ch-01" / "sec-01"
    sec1_dir.mkdir(parents=True)
    (sec1_dir / "lesson-plan.md").write_text("# Instructor Secrets", encoding="utf-8")
    (sec1_dir / "notes.md").write_text("# Student Notes", encoding="utf-8")
    (course_dir / "test-ledger.jsonl").write_text('{"entry": 1}\n', encoding="utf-8")

    result = run_context("get-manifest", "--skill", "tc-test-me", "--path", str(course_dir))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["skill"] == "tc-test-me"

    files = data["authorized_files"]
    # NEVER include lesson-plan.md
    assert not any("lesson-plan.md" in f for f in files)
    # Include notes and ledger
    assert any("notes.md" in f for f in files)
    assert any("test-ledger.jsonl" in f for f in files)


def test_get_manifest_tc_practicals_omits_lesson_plans(tmp_path: Path):
    """Verify tc-practicals loads course.toml and completed notes, but omits lesson plans."""
    course_dir = tmp_path / "course-practicals"
    course_dir.mkdir(parents=True)

    manifest_file = course_dir / "course.toml"
    content = """
[course]
slug = "practical-course"
title = "Practical Course"
status = "in_progress"

[[chapters]]
id = 1
slug = "ch-01"
title = "Ch 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Sec 1"
status = "completed"
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    sec1_dir = course_dir / "ch-01" / "sec-01"
    sec1_dir.mkdir(parents=True)
    (sec1_dir / "lesson-plan.md").write_text("# LP", encoding="utf-8")
    (sec1_dir / "notes.md").write_text("# Notes", encoding="utf-8")

    result = run_context("get-manifest", "--skill", "tc-practicals", "--path", str(course_dir))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    files = data["authorized_files"]
    assert not any("lesson-plan.md" in f for f in files)
    assert any("course.toml" in f for f in files)


def test_get_manifest_tc_create_omits_notes_and_lesson_plans(tmp_path: Path):
    """Verify tc-create omits lesson plans and notes."""
    result = run_context("get-manifest", "--skill", "tc-create", "--path", str(tmp_path))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    files = data["authorized_files"]
    assert not any("lesson-plan.md" in f for f in files)
    assert not any("notes.md" in f for f in files)


def test_get_manifest_tc_verify_course_includes_lesson_plans(tmp_path: Path):
    """Verify tc-verify-course loads all drafted lesson-plan.md files and omits notes."""
    course_dir = tmp_path / "course-verify"
    course_dir.mkdir(parents=True)

    manifest_file = course_dir / "course.toml"
    manifest_file.write_text('[course]\nslug = "v"\ntitle = "V"\nstatus = "not_started"\n', encoding="utf-8")

    ch_dir = course_dir / "ch-01" / "sec-01"
    ch_dir.mkdir(parents=True)
    lp_file = ch_dir / "lesson-plan.md"
    lp_file.write_text("# Draft Plan", encoding="utf-8")

    result = run_context("get-manifest", "--skill", "tc-verify-course", "--path", str(course_dir))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    files = data["authorized_files"]
    assert any("lesson-plan.md" in f for f in files)
    assert not any("notes.md" in f for f in files)
    assert not any("test-ledger.jsonl" in f for f in files)


def test_check_tc_test_me_rejects_lesson_plan():
    """Verify check rejects lesson-plan.md for tc-test-me (prevents concept leaks)."""
    result = run_context("check", "--skill", "tc-test-me", "--file", "future/lesson-plan.md")
    assert result.returncode == 1
    data = json.loads(result.stderr)
    assert data["authorized"] is False
    assert "Future section access forbidden" in data["reason"]


def test_check_tc_teach_allows_active_lesson_plan(tmp_path: Path):
    """Verify check authorizes active section lesson-plan.md for tc-teach."""
    course_dir = tmp_path / "course-teach"
    course_dir.mkdir(parents=True)

    manifest_file = course_dir / "course.toml"
    content = """
[course]
slug = "teach-check"
title = "Teach Check"
status = "in_progress"

[[chapters]]
id = 1
slug = "ch-01"
title = "Ch 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Sec 1"
status = "in_progress"
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    sec_dir = course_dir / "ch-01" / "sec-01"
    sec_dir.mkdir(parents=True)
    lp_file = sec_dir / "lesson-plan.md"
    lp_file.write_text("# Active LP", encoding="utf-8")

    result = run_context(
        "check",
        "--skill", "tc-teach",
        "--file", str(lp_file),
        "--path", str(course_dir),
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["authorized"] is True


def test_check_tc_teach_rejects_out_of_scope_lesson_plan(tmp_path: Path):
    """Verify check rejects future/out-of-scope section lesson-plan.md for tc-teach."""
    course_dir = tmp_path / "course-teach-reject"
    course_dir.mkdir(parents=True)

    manifest_file = course_dir / "course.toml"
    content = """
[course]
slug = "teach-check"
title = "Teach Check"
status = "in_progress"

[[chapters]]
id = 1
slug = "ch-01"
title = "Ch 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Sec 1"
status = "in_progress"

[[chapters.sections]]
id = 2
slug = "sec-02"
title = "Sec 2"
status = "not_started"
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    future_lp = course_dir / "ch-01" / "sec-02" / "lesson-plan.md"
    result = run_context(
        "check",
        "--skill", "tc-teach",
        "--file", str(future_lp),
        "--path", str(course_dir),
    )
    assert result.returncode == 1
    data = json.loads(result.stderr)
    assert data["authorized"] is False
    assert "Future section access forbidden" in data["reason"]


def test_check_future_keyword_path_rejected():
    """Verify any file path mentioning future is rejected across skills."""
    result = run_context("check", "--skill", "tc-teach", "--file", "future/section-05/notes.md")
    assert result.returncode == 1
    data = json.loads(result.stderr)
    assert data["authorized"] is False
    assert "Future section access forbidden" in data["reason"]


def test_check_tc_practicals_rejects_lesson_plan():
    """Verify tc-practicals rejects lesson-plan.md files."""
    result = run_context("check", "--skill", "tc-practicals", "--file", "section-01/lesson-plan.md")
    assert result.returncode == 1
    data = json.loads(result.stderr)
    assert data["authorized"] is False


def test_unknown_skill_rejected():
    """Verify unknown skill name fails with clean error message."""
    result = run_context("get-manifest", "--skill", "unknown-skill")
    assert result.returncode == 1
    data = json.loads(result.stderr)
    assert data["ok"] is False
    assert "Unknown skill" in data["error"]


def test_matrix_subcommand():
    """Verify matrix subcommand lists Stage Loading Matrix across skills."""
    result = run_context("matrix")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "tc-teach" in data
    assert "tc-test-me" in data
    assert "tc-practicals" in data
    assert "tc-create" in data
    assert "tc-verify-course" in data
    assert data["tc-teach"]["budget_tokens"] <= 4000
