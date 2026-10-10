"""tests/test_course_builder.py — Comprehensive test suite for course scaffolding and Triad Consensus."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

BUILDER_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "course_builder.py"
SKILL_FILE = Path(__file__).parent.parent / "skills" / "tc-create" / "SKILL.md"


def test_builder_cli_help():
    """Verify course_builder CLI prints help message and exits 0."""
    res = subprocess.run([sys.executable, str(BUILDER_SCRIPT), "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "create" in res.stdout
    assert "archetypes" in res.stdout


def test_builder_archetypes_subcommand():
    """Verify archetypes subcommand lists all 5 Universal Archetypes."""
    res = subprocess.run([sys.executable, str(BUILDER_SCRIPT), "archetypes", "--json"], capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    archetypes = data["archetypes"]
    assert "applied_creation" in archetypes
    assert "forensic_dilemma" in archetypes
    assert "axiomatic_primitives" in archetypes
    assert "spiral_immersion" in archetypes
    assert "reverse_engineering" in archetypes


def test_builder_pep_723_metadata():
    """Verify script contains valid PEP 723 metadata header."""
    content = BUILDER_SCRIPT.read_text(encoding="utf-8")
    assert "# /// script" in content
    assert 'requires-python = ">=3.11"' in content
    assert "tomli-w>=" in content
    assert "# ///" in content


def test_zero_bmad_references():
    """Verify strict zero-BMad references in scripts and skill documentation."""
    for target in [BUILDER_SCRIPT, SKILL_FILE]:
        text = target.read_text(encoding="utf-8")
        assert not re.search(r"\bbmad\b", text, re.IGNORECASE), f"Found BMad mention in {target}"


def test_create_course_scaffolds_filesystem_correctly(tmp_path: Path):
    """Verify create coordinates Triad loop, appends trace, and scaffolds files without notes.md."""
    res = subprocess.run(
        [
            sys.executable,
            str(BUILDER_SCRIPT),
            "create",
            "--slug",
            "sqlite-clone",
            "--title",
            "Build an SQLite Clone",
            "--archetype",
            "applied_creation",
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
    assert data["consensus_reached"] is True

    course_dir = tmp_path / "courses" / "sqlite-clone"
    assert course_dir.is_dir()

    manifest_file = course_dir / "course.toml"
    overview_file = course_dir / "overview.md"
    assert manifest_file.is_file()
    assert overview_file.is_file()

    # Check overview content
    overview_text = overview_file.read_text(encoding="utf-8")
    assert "Build an SQLite Clone" in overview_text
    assert "Applied Creation" in overview_text

    # Check consensus trace
    trace_file = tmp_path / ".tc" / "cache" / "consensus-trace.jsonl"
    assert trace_file.is_file()
    lines = trace_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    last_record = json.loads(lines[-1])
    assert last_record["slug"] == "sqlite-clone"
    assert last_record["consensus_reached"] is True

    # Check chapter directories and lesson-plan.md
    chapter_dirs = list(course_dir.glob("chapter-*"))
    assert len(chapter_dirs) >= 4
    for ch_d in chapter_dirs:
        sec_dirs = list(ch_d.glob("section-*"))
        assert len(sec_dirs) >= 1
        for s_d in sec_dirs:
            assert (s_d / "lesson-plan.md").is_file()
            # CRITICAL INVARIANT: notes.md must NOT exist prior to student completion!
            assert not (s_d / "notes.md").exists()


@pytest.mark.parametrize(
    "archetype",
    [
        "applied_creation",
        "forensic_dilemma",
        "axiomatic_primitives",
        "spiral_immersion",
        "reverse_engineering",
    ],
)
def test_create_all_archetypes(tmp_path: Path, archetype: str):
    """Verify all 5 Universal Archetypes pass Triad Consensus and scaffold cleanly."""
    slug = f"course-{archetype.replace('_', '-')}"
    res = subprocess.run(
        [
            sys.executable,
            str(BUILDER_SCRIPT),
            "create",
            "--slug",
            slug,
            "--archetype",
            archetype,
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
    assert (tmp_path / "courses" / slug / "course.toml").is_file()


def test_create_with_outline_file_ingestion(tmp_path: Path):
    """Verify course builder ingests user-supplied syllabus outline markdown."""
    outline_file = tmp_path / "syllabus.md"
    outline_file.write_text(
        "# Chapter 1: Foundations\n"
        "- Memory Allocators\n"
        "- Pointer Arithmetic\n\n"
        "# Chapter 2: Virtual Memory\n"
        "- Page Tables\n"
        "- TLB Caching\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            str(BUILDER_SCRIPT),
            "create",
            "--slug",
            "os-memory",
            "--archetype",
            "axiomatic_primitives",
            "--outline-file",
            str(outline_file),
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

    overview_text = (tmp_path / "courses" / "os-memory" / "overview.md").read_text(encoding="utf-8")
    assert "Foundations" in overview_text
    assert "Virtual Memory" in overview_text
