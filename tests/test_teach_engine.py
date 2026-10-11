"""tests/test_teach_engine.py — Comprehensive test suite for conversational teaching engine."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import tomli_w

TEACH_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "teach_engine.py"
SKILL_FILE = Path(__file__).parent.parent / "skills" / "tc-teach" / "SKILL.md"


def test_teach_cli_help():
    """Verify teach_engine CLI prints help message and exits 0."""
    res = subprocess.run([sys.executable, str(TEACH_SCRIPT), "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "session" in res.stdout
    assert "advance" in res.stdout
    assert "fork" in res.stdout


def test_teach_fork_subcommand():
    """Verify fork outputs standardized 4-option Next-Action Fork."""
    res = subprocess.run([sys.executable, str(TEACH_SCRIPT), "fork", "--json"], capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert "Next Action Fork" in data["text"]
    assert "`[1]` **Next Concept**" in data["text"]
    assert "`[2]` **Test Me**" in data["text"]
    assert len(data["options"]) == 4


def test_teach_pep_723_metadata():
    """Verify script contains valid PEP 723 metadata header."""
    content = TEACH_SCRIPT.read_text(encoding="utf-8")
    assert "# /// script" in content
    assert 'requires-python = ">=3.11"' in content
    assert "tomli-w>=" in content
    assert "# ///" in content


def test_zero_bmad_references():
    """Verify strict zero-BMad references in scripts and skill prompt."""
    for target in [TEACH_SCRIPT, SKILL_FILE]:
        text = target.read_text(encoding="utf-8")
        assert not re.search(r"\bbmad\b", text, re.IGNORECASE), f"Found BMad mention in {target}"


def test_teaching_session_and_advance_flow(tmp_path: Path):
    """Verify teach_engine resolves active session, ticks concepts, and compiles notes on final item."""
    # Set up preferences
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir(parents=True)
    (plan_dir / "preferences.md").write_text(
        "---\nstyle_profile: direct_technical\ndensity: example_driven\n---\n",
        encoding="utf-8",
    )

    # Set up course
    course_dir = tmp_path / "courses" / "rust-memory"
    sec_dir = course_dir / "chapter-01" / "section-01"
    sec_dir.mkdir(parents=True)

    manifest_data = {
        "course": {"id": "rust-memory", "title": "Rust Memory", "status": "in_progress"},
        "chapters": [
            {
                "id": "chapter-01",
                "title": "Stack vs Heap",
                "sections": [
                    {"id": "sec-01", "title": "Stack Layout", "status": "in_progress"}
                ],
            }
        ],
    }
    with open(course_dir / "course.toml", "wb") as f:
        tomli_w.dump(manifest_data, f)

    # Set up lesson plan with 2 concepts
    (sec_dir / "lesson-plan.md").write_text(
        "# Lesson Plan\n\n"
        "## Concepts\n"
        "- [ ] Stack frames and pointer offsets\n"
        "- [ ] Heap allocations via Box\n",
        encoding="utf-8",
    )

    # 1. Inspect session
    res_sess = subprocess.run(
        [
            sys.executable,
            str(TEACH_SCRIPT),
            "session",
            "--course",
            "rust-memory",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_sess.returncode == 0
    d_sess = json.loads(res_sess.stdout)
    assert d_sess["ok"] is True
    assert d_sess["active_section"]["section_title"] == "Stack Layout"
    assert d_sess["active_concept"]["concept"] == "Stack frames and pointer offsets"
    assert d_sess["preferences"]["style_profile"] == "direct_technical"

    # 2. Advance first concept
    res_adv1 = subprocess.run(
        [
            sys.executable,
            str(TEACH_SCRIPT),
            "advance",
            "--course",
            "rust-memory",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_adv1.returncode == 0
    d_adv1 = json.loads(res_adv1.stdout)
    assert d_adv1["section_fully_completed"] is False
    assert d_adv1["remaining_concepts"] == 1
    assert not (sec_dir / "notes.md").exists()

    # 3. Advance second (final) concept -> triggers notes compilation!
    res_adv2 = subprocess.run(
        [
            sys.executable,
            str(TEACH_SCRIPT),
            "advance",
            "--course",
            "rust-memory",
            "--workspace",
            str(tmp_path),
            "--recap",
            "Stack allocations have zero runtime overhead.",
            "Box moves allocations to heap.",
            "Lifetimes track stack frame validity.",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_adv2.returncode == 0
    d_adv2 = json.loads(res_adv2.stdout)
    assert d_adv2["section_fully_completed"] is True
    assert d_adv2["next_recommendation"] == "/tc-test-me"

    # Verify notes.md was automatically compiled
    notes_file = sec_dir / "notes.md"
    assert notes_file.is_file()
    notes_text = notes_file.read_text(encoding="utf-8")
    assert "Stack Layout" in notes_text
    assert "3-Bullet Recap" in notes_text
    assert "zero runtime overhead" in notes_text

    # Verify course.toml was updated to review status
    import tomllib
    updated_manifest = tomllib.loads((course_dir / "course.toml").read_text(encoding="utf-8"))
    assert updated_manifest["chapters"][0]["sections"][0]["status"] == "review"


def test_resolve_active_section_skips_review_when_not_started_present(tmp_path: Path):
    """Verify that teach_engine does not loop on completed review section when not_started section exists."""
    course_dir = tmp_path / "courses" / "flow-test"
    course_dir.mkdir(parents=True)
    (course_dir / "chapter-01" / "section-01").mkdir(parents=True)
    (course_dir / "chapter-01" / "section-02").mkdir(parents=True)

    manifest_data = {
        "course": {"id": "flow-test", "title": "Flow Test", "status": "in_progress"},
        "chapters": [
            {
                "id": "chapter-01",
                "title": "Ch 1",
                "sections": [
                    {"id": "sec-01", "title": "Sec 1", "status": "review"},
                    {"id": "sec-02", "title": "Sec 2", "status": "not_started"},
                ],
            }
        ],
    }
    with open(course_dir / "course.toml", "wb") as f:
        tomli_w.dump(manifest_data, f)

    res = subprocess.run(
        [
            sys.executable,
            str(TEACH_SCRIPT),
            "session",
            "--course",
            "flow-test",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    # Must select section 2 (not_started), NOT section 1 (review)
    assert data["active_section"]["section_id"] == "sec-02"
    assert data["active_section"]["section_status"] == "not_started"


def test_integer_ids_compatibility(tmp_path: Path):
    """Verify that integer chapter and section IDs in manifest do not cause TypeErrors."""
    course_dir = tmp_path / "courses" / "int-ids"
    course_dir.mkdir(parents=True)
    (course_dir / "chapter-01" / "section-01").mkdir(parents=True)

    manifest_data = {
        "course": {"id": "int-ids", "title": "Int IDs Test", "status": "in_progress"},
        "chapters": [
            {
                "id": 1,
                "title": "Chapter 1",
                "sections": [
                    {"id": 1, "title": "Section 1", "status": "in_progress"},
                ],
            }
        ],
    }
    with open(course_dir / "course.toml", "wb") as f:
        tomli_w.dump(manifest_data, f)

    res = subprocess.run(
        [
            sys.executable,
            str(TEACH_SCRIPT),
            "session",
            "--course",
            "int-ids",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["active_section"]["chapter_id"] == 1
    assert data["active_section"]["section_id"] == 1

