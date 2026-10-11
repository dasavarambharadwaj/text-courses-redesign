"""tests/test_streamline_layout.py — Tests for streamlined sovereign filesystem layout (FR-29).

Validates:
- Workspace bootstrapping creates visible _tc/, profile/, roadmap/ layout with memlog.md
- Course scaffolding creates notes/ directory with chapter-XX.md and course memlog.md
- Notes compiler compiles both section notes.md and flat chapter textbook notes/chapter-XX.md
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import tomli_w

SCRIPTS_DIR = Path(__file__).parent.parent / "_tc" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from bootstrapper import bootstrap_workspace
from course_builder import create_course, scaffold_course_files
from notes_compiler import compile_notes


def test_bootstrap_workspace_creates_streamlined_layout(tmp_path: Path):
    """Verify bootstrap creates visible _tc/, profile/, and roadmap/ directories."""
    res = bootstrap_workspace(
        path=tmp_path,
        role="Systems Engineer",
        domain_experience="Intermediate",
    )
    assert res["ok"] is True

    # Check visible engine root _tc/
    assert (tmp_path / "_tc").is_dir()
    assert (tmp_path / "_tc" / "cache").is_dir()
    assert (tmp_path / "_tc" / "research").is_dir()
    assert (tmp_path / "_tc" / "scripts").is_dir()
    assert (tmp_path / "_tc" / "config.json").is_file()

    # Check profile and global memlog
    assert (tmp_path / "profile").is_dir()
    assert (tmp_path / "profile" / "preferences.md").is_file()
    assert (tmp_path / "profile" / "memlog.md").is_file()
    profile_memlog_content = (tmp_path / "profile" / "memlog.md").read_text(encoding="utf-8")
    assert "type: global-memlog" in profile_memlog_content

    # Check roadmap dir
    assert (tmp_path / "roadmap").is_dir()


def test_course_scaffolding_creates_flat_notes_and_memlog(tmp_path: Path):
    """Verify course scaffolding creates notes/chapter-XX.md and course memlog.md."""
    course_data = {
        "course": {
            "id": "compilers-101",
            "title": "Compilers 101",
            "archetype": "applied_creation",
            "status": "in_progress",
        },
        "chapters": [
            {
                "id": "ch-01",
                "title": "Lexing & AST",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "Token Streams",
                        "status": "in_progress",
                        "prerequisites": [],
                        "vocabulary_introduced": ["Token", "Lexer"],
                    }
                ],
            }
        ],
    }

    course_dir = scaffold_course_files(tmp_path, course_data)
    assert course_dir.is_dir()

    # Flat chapter notes
    notes_dir = course_dir / "notes"
    assert notes_dir.is_dir()
    assert (notes_dir / "chapter-01.md").is_file()
    chapter_notes_text = (notes_dir / "chapter-01.md").read_text(encoding="utf-8")
    assert "# Chapter 01 Notes" in chapter_notes_text

    # Course memlog
    course_memlog = course_dir / "memlog.md"
    assert course_memlog.is_file()
    memlog_text = course_memlog.read_text(encoding="utf-8")
    assert "course: compilers-101" in memlog_text


def test_notes_compiler_updates_flat_chapter_notes(tmp_path: Path):
    """Verify notes compilation writes section notes.md AND updates flat chapter textbook."""
    course_dir = tmp_path / "courses" / "os-dev"
    sec_dir = course_dir / "chapter-01-kernel" / "section-01-boot"
    sec_dir.mkdir(parents=True)

    manifest_data = {
        "course": {
            "id": "os-dev",
            "title": "Operating Systems",
            "status": "in_progress",
        },
        "chapters": [
            {
                "id": "ch-01",
                "title": "Kernel Bootstrap",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "Bootloader Handoff",
                        "status": "in_progress",
                    }
                ],
            }
        ],
    }
    with open(course_dir / "course.toml", "wb") as f:
        tomli_w.dump(manifest_data, f)

    res = compile_notes(
        section_dir=sec_dir,
        title="Bootloader Handoff",
        recap=["Protected mode sets up GDT and IDT.", "A20 line must be enabled."],
        content="Kernel entry point requires 32-bit flat memory model.",
        examples="mov ax, 0x10; mov ds, ax;",
        pitfalls="Triple fault if IDT is not loaded before enabling interrupts.",
    )

    assert res["ok"] is True
    # Verify section notes.md
    assert (sec_dir / "notes.md").is_file()

    # Verify flat chapter textbook
    flat_notes_file = course_dir / "notes" / "chapter-01.md"
    assert flat_notes_file.is_file()
    flat_content = flat_notes_file.read_text(encoding="utf-8")
    assert "Bootloader Handoff" in flat_content
    assert "Protected mode sets up GDT" in flat_content
