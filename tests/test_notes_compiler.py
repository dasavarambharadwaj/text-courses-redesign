"""tests/test_notes_compiler.py — Comprehensive test suite for notes compiler and section transition."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import tomli_w

COMPILER_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "notes_compiler.py"


def test_compiler_cli_help():
    """Verify notes_compiler CLI prints help message and exits 0."""
    res = subprocess.run([sys.executable, str(COMPILER_SCRIPT), "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "compile" in res.stdout
    assert "inspect" in res.stdout


def test_compiler_pep_723_metadata():
    """Verify script contains valid PEP 723 metadata header."""
    content = COMPILER_SCRIPT.read_text(encoding="utf-8")
    assert "# /// script" in content
    assert 'requires-python = ">=3.11"' in content
    assert "tomli-w>=" in content
    assert "# ///" in content


def test_zero_bmad_references():
    """Verify strict zero-BMad references in scripts and test suite."""
    text = COMPILER_SCRIPT.read_text(encoding="utf-8")
    assert not re.search(r"\bbmad\b", text, re.IGNORECASE), f"Found BMad mention in {COMPILER_SCRIPT}"


def test_compile_notes_and_transitions_manifest(tmp_path: Path):
    """Verify compile writes notes.md with 3-bullet recap and transitions section to review status."""
    course_dir = tmp_path / "courses" / "async-rust"
    sec_dir = course_dir / "chapter-01-intro" / "section-01-tokio"
    sec_dir.mkdir(parents=True)

    manifest_data = {
        "course": {
            "id": "async-rust",
            "title": "Async Rust Systems",
            "status": "in_progress",
        },
        "chapters": [
            {
                "id": "ch-01",
                "title": "Introduction",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "Tokio Fundamentals",
                        "status": "in_progress",
                    }
                ],
            }
        ],
    }
    course_toml = course_dir / "course.toml"
    with open(course_toml, "wb") as f:
        tomli_w.dump(manifest_data, f)

    recap_bullets = [
        "Async runtimes schedule cooperative tasks over work-stealing threads.",
        "Blocking calls in worker threads cause starvation without spawn_blocking.",
        "TaskGroups manage structured concurrency with failure propagation.",
    ]

    res = subprocess.run(
        [
            sys.executable,
            str(COMPILER_SCRIPT),
            "compile",
            "--section-dir",
            str(sec_dir),
            "--title",
            "Tokio Fundamentals",
            "--recap",
            *recap_bullets,
            "--content",
            "Detailed mechanics of epoll event loop integration.",
            "--examples",
            "tokio::spawn(async { ... });",
            "--pitfalls",
            "Never call std::thread::sleep inside async block.",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["section_status"] == "review"
    assert data["course_manifest_updated"] is True

    # 1. Verify notes.md content
    notes_file = sec_dir / "notes.md"
    assert notes_file.is_file()
    notes_text = notes_file.read_text(encoding="utf-8")
    assert "# Tokio Fundamentals" in notes_text
    assert "## 3-Bullet Recap" in notes_text
    assert "work-stealing threads" in notes_text
    assert "spawn_blocking" in notes_text
    assert "## Core Mechanics & Architecture" in notes_text
    assert "## Worked Examples & Concrete Implementation" in notes_text
    assert "## Common Pitfalls & Fatal Mistakes" in notes_text

    # 2. Verify course.toml was updated to review status
    import tomllib
    updated_manifest = tomllib.loads(course_toml.read_text(encoding="utf-8"))
    sec_record = updated_manifest["chapters"][0]["sections"][0]
    assert sec_record["status"] == "review"
    assert "updated" in sec_record


def test_compile_collision_refuses_overwrite(tmp_path: Path):
    """Verify compile refuses to overwrite existing notes without --force."""
    sec_dir = tmp_path / "section-01"
    sec_dir.mkdir(parents=True)
    existing_notes = sec_dir / "notes.md"
    existing_notes.write_text("# Existing Permanent Notes\nDo not overwrite!\n", encoding="utf-8")

    # Call without force
    res = subprocess.run(
        [
            sys.executable,
            str(COMPILER_SCRIPT),
            "compile",
            "--section-dir",
            str(sec_dir),
            "--title",
            "Overwriting Title",
            "--recap",
            "Bullet 1",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    data = json.loads(res.stderr)
    assert data["ok"] is False
    assert data["already_exists"] is True
    assert existing_notes.read_text(encoding="utf-8") == "# Existing Permanent Notes\nDo not overwrite!\n"

    # Call with force succeeds
    res_force = subprocess.run(
        [
            sys.executable,
            str(COMPILER_SCRIPT),
            "compile",
            "--section-dir",
            str(sec_dir),
            "--title",
            "New Forced Title",
            "--recap",
            "Bullet 1",
            "--force",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_force.returncode == 0
    assert "# New Forced Title" in existing_notes.read_text(encoding="utf-8")


def test_inspect_notes_state(tmp_path: Path):
    """Verify inspect reports compilation status accurately."""
    sec_dir = tmp_path / "section-02"
    sec_dir.mkdir(parents=True)

    # 1. Uncompiled section
    res1 = subprocess.run(
        [sys.executable, str(COMPILER_SCRIPT), "inspect", "--section-dir", str(sec_dir), "--json"],
        capture_output=True,
        text=True,
    )
    assert res1.returncode == 0
    d1 = json.loads(res1.stdout)
    assert d1["compiled"] is False

    # 2. Compile section
    subprocess.run(
        [
            sys.executable,
            str(COMPILER_SCRIPT),
            "compile",
            "--section-dir",
            str(sec_dir),
            "--title",
            "Inspection Test",
            "--recap",
            "Point 1",
            "Point 2",
        ],
        capture_output=True,
        text=True,
    )

    # 3. Compiled section inspect
    res2 = subprocess.run(
        [sys.executable, str(COMPILER_SCRIPT), "inspect", "--section-dir", str(sec_dir), "--json"],
        capture_output=True,
        text=True,
    )
    assert res2.returncode == 0
    d2 = json.loads(res2.stdout)
    assert d2["compiled"] is True
    assert d2["recap_bullets_count"] == 2
    assert d2["size_bytes"] > 0
