"""tests/test_clean_workspace.py — Verification of Two-Tier Clean Workspace Substrate (CAP-4)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from course_builder import create_course
from manifest import resolve_manifest_path, find_course_file, get_engine_dir
from teach_engine import find_section_directory, resolve_active_section


def test_new_course_scaffolds_clean_hierarchy(tmp_path: Path):
    """Verify newly created course has clean human canvas at root and machine substrate inside .tc/."""
    slug = "serene-arch"
    res = create_course(
        slug=slug,
        title="Serene Architecture",
        archetype="applied_creation",
        workspace=tmp_path,
    )
    assert res["ok"] is True
    course_dir = Path(res["course_path"])

    # 1. Human canvas root check: only overview.md, notes/, and .tc/
    root_items = set(p.name for p in course_dir.iterdir())
    assert root_items == {"overview.md", "notes", ".tc"}
    assert (course_dir / "overview.md").is_file()
    assert (course_dir / "notes").is_dir()
    assert (course_dir / "notes" / "chapter-01.md").is_file()

    # 2. Machine substrate encapsulation check inside .tc/
    tc_dir = course_dir / ".tc"
    assert tc_dir.is_dir()
    assert (tc_dir / "course.toml").is_file()
    assert (tc_dir / "consensus-deliberation.md").is_file()
    assert (tc_dir / "curriculum-brainstorm.md").is_file()
    assert (tc_dir / "memlog.md").is_file()
    assert (tc_dir / "plans").is_dir()

    # Verify lesson plan is inside .tc/plans
    plans = list((tc_dir / "plans").glob("**/lesson-plan.md"))
    assert len(plans) > 0


def test_dual_path_search_fallback_legacy_course(tmp_path: Path):
    """Verify legacy courses without .tc/ load seamlessly through backwards compatibility."""
    course_dir = tmp_path / "courses" / "legacy-course"
    course_dir.mkdir(parents=True, exist_ok=True)

    # Place machine files at root (legacy layout)
    course_toml = course_dir / "course.toml"
    course_toml.write_text(
        """[course]
id = "legacy-course"
slug = "legacy-course"
title = "Legacy Architecture"
archetype = "applied_creation"
status = "in_progress"

[[chapters]]
id = "chapter-01"
title = "Foundations"

[[chapters.sections]]
id = "sec-01"
title = "Primitive Allocations"
status = "in_progress"
vocabulary_introduced = ["allocator"]
""",
        encoding="utf-8",
    )

    sec_dir = course_dir / "chapter-01" / "section-01"
    sec_dir.mkdir(parents=True, exist_ok=True)
    (sec_dir / "lesson-plan.md").write_text("# Lesson Plan: Primitive Allocations\n- [ ] Verify allocator.\n", encoding="utf-8")

    # Verify resolve_manifest_path falls back to root
    resolved = resolve_manifest_path(course_dir)
    assert resolved == course_toml

    # Verify find_section_directory finds legacy section
    found_sec = find_section_directory(course_dir, "chapter-01", "sec-01")
    assert found_sec is not None
    assert found_sec == sec_dir

    # Verify resolve_active_section succeeds
    active = resolve_active_section(course_dir)
    assert active["section_id"] == "sec-01"


def test_dual_path_search_encapsulated_course(tmp_path: Path):
    """Verify engine scripts resolve encapsulated .tc/ directory files first."""
    course_dir = tmp_path / "courses" / "encapsulated-course"
    tc_dir = course_dir / ".tc"
    tc_dir.mkdir(parents=True, exist_ok=True)

    course_toml = tc_dir / "course.toml"
    course_toml.write_text(
        """[course]
id = "encapsulated-course"
slug = "encapsulated-course"
title = "Encapsulated Design"
archetype = "applied_creation"
status = "in_progress"

[[chapters]]
id = "chapter-01"
title = "Clean Substrate"

[[chapters.sections]]
id = "sec-01"
title = "Hidden State"
status = "in_progress"
vocabulary_introduced = ["encapsulation"]
""",
        encoding="utf-8",
    )

    sec_dir = tc_dir / "plans" / "chapter-01" / "section-01"
    sec_dir.mkdir(parents=True, exist_ok=True)
    (sec_dir / "lesson-plan.md").write_text("# Lesson Plan: Hidden State\n- [ ] Verify encapsulation.\n", encoding="utf-8")

    # Verify resolve_manifest_path finds .tc/course.toml
    resolved = resolve_manifest_path(course_dir)
    assert resolved == course_toml

    # Verify find_section_directory finds section inside .tc/plans
    found_sec = find_section_directory(course_dir, "chapter-01", "sec-01")
    assert found_sec is not None
    assert found_sec == sec_dir

    # Verify resolve_active_section finds section inside .tc/
    active = resolve_active_section(course_dir)
    assert active["section_id"] == "sec-01"
    assert active["section_title"] == "Hidden State"


def test_manifest_advance_cli_on_encapsulated_course(tmp_path: Path):
    """Verify manifest.py advance works on encapsulated courses."""
    course_dir = tmp_path / "courses" / "active-course"
    tc_dir = course_dir / ".tc"
    tc_dir.mkdir(parents=True, exist_ok=True)

    course_toml = tc_dir / "course.toml"
    course_toml.write_text(
        """[course]
id = "active-course"
slug = "active-course"
title = "Active Course"
archetype = "applied_creation"
status = "in_progress"

[[chapters]]
id = "chapter-01"
title = "Chapter 1"

[[chapters.sections]]
id = "sec-01"
title = "Section 1"
status = "in_progress"
""",
        encoding="utf-8",
    )

    manifest_py = SCRIPTS_DIR / "manifest.py"
    cmd = [
        sys.executable,
        str(manifest_py),
        "advance",
        "--path",
        str(course_dir),
        "--chapter",
        "1",
        "--section",
        "1",
        "--status",
        "completed",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["status"] == "completed"
