import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

MANIFEST_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "manifest.py"


def run_manifest(*args: str) -> subprocess.CompletedProcess[str]:
    """Helper to run manifest.py CLI and capture stdout/stderr."""
    cmd = [sys.executable, str(MANIFEST_SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_manifest_help():
    """Verify help subcommand displays usage."""
    result = run_manifest("--help")
    assert result.returncode == 0
    assert "TextCourses atomic manifest manager" in result.stdout
    assert "init-course" in result.stdout
    assert "init-roadmap" in result.stdout
    assert "get-status" in result.stdout
    assert "advance" in result.stdout
    assert "validate" in result.stdout


def test_init_course_success(tmp_path: Path):
    """Verify init-course creates a valid course.toml."""
    course_dir = tmp_path / "course-rust"
    result = run_manifest(
        "init-course",
        "--path", str(course_dir),
        "--slug", "rust-primer",
        "--title", "Rust Primer",
        "--archetype", "systems_engineering",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["slug"] == "rust-primer"
    assert data["title"] == "Rust Primer"

    manifest_file = course_dir / "course.toml"
    assert manifest_file.exists()

    with open(manifest_file, "rb") as f:
        toml_data = tomllib.load(f)

    assert toml_data["course"]["slug"] == "rust-primer"
    assert toml_data["course"]["title"] == "Rust Primer"
    assert toml_data["course"]["status"] == "not_started"
    assert toml_data["course"]["archetype"] == "systems_engineering"
    assert "created" in toml_data["course"]
    assert "updated" in toml_data["course"]
    assert toml_data["chapters"] == []


def test_init_roadmap_success(tmp_path: Path):
    """Verify init-roadmap creates a valid roadmap.toml."""
    roadmap_dir = tmp_path / "track-backend"
    result = run_manifest(
        "init-roadmap",
        "--path", str(roadmap_dir),
        "--title", "Backend Mastery Track",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["title"] == "Backend Mastery Track"

    manifest_file = roadmap_dir / "roadmap.toml"
    assert manifest_file.exists()

    with open(manifest_file, "rb") as f:
        toml_data = tomllib.load(f)

    assert toml_data["roadmap"]["title"] == "Backend Mastery Track"
    assert toml_data["roadmap"]["status"] == "not_started"
    assert toml_data["roadmap"]["courses"] == []


def test_get_status_missing_manifest(tmp_path: Path):
    """Verify get-status fails gracefully when manifest is missing."""
    empty_dir = tmp_path / "nonexistent"
    result = run_manifest("get-status", "--path", str(empty_dir))
    assert result.returncode == 1
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert "Manifest not found" in err_data["error"]


def test_get_status_course(tmp_path: Path):
    """Verify get-status computes progress metrics across chapters and sections."""
    course_dir = tmp_path / "course-sample"
    run_manifest(
        "init-course",
        "--path", str(course_dir),
        "--slug", "sample-course",
        "--title", "Sample Course",
    )

    manifest_file = course_dir / "course.toml"
    # Populate dummy chapters and sections
    content = """
[course]
slug = "sample-course"
title = "Sample Course"
status = "in_progress"
created = "2026-10-10T00:00:00Z"
updated = "2026-10-10T00:00:00Z"
archetype = "applied_creation"

[[chapters]]
id = 1
slug = "ch-01-foundations"
title = "Foundations"

[[chapters.sections]]
id = 1
slug = "sec-01-intro"
title = "Intro"
status = "completed"

[[chapters.sections]]
id = 2
slug = "sec-02-core"
title = "Core Concepts"
status = "in_progress"

[[chapters]]
id = 2
slug = "ch-02-advanced"
title = "Advanced"

[[chapters.sections]]
id = 1
slug = "sec-01-deep-dive"
title = "Deep Dive"
status = "not_started"
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_manifest("get-status", "--path", str(course_dir))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["type"] == "course"
    assert data["total_chapters"] == 2
    assert data["total_sections"] == 3
    assert data["completed_sections"] == 1
    assert data["active_chapter"]["id"] == 1
    assert data["active_section"]["slug"] == "sec-02-core"


def test_advance_section_and_course_lifecycle(tmp_path: Path):
    """Verify advancing sections updates timestamps and course status."""
    course_dir = tmp_path / "course-advance"
    manifest_file = course_dir / "course.toml"
    course_dir.mkdir(parents=True)

    content = """
[course]
slug = "lifecycle-course"
title = "Lifecycle Course"
status = "not_started"
created = "2026-10-10T00:00:00Z"
updated = "2026-10-10T00:00:00Z"
archetype = "applied_creation"

[[chapters]]
id = 1
slug = "ch-01"
title = "Chapter 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Section 1"
status = "not_started"

[[chapters.sections]]
id = 2
slug = "sec-02"
title = "Section 2"
status = "not_started"
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    # Advance section 1 to in_progress
    res1 = run_manifest(
        "advance",
        "--path", str(manifest_file),
        "--chapter", "1",
        "--section", "1",
        "--status", "in_progress",
    )
    assert res1.returncode == 0
    data1 = json.loads(res1.stdout)
    assert data1["ok"] is True
    assert data1["course_status"] == "in_progress"

    # Advance section 1 to completed
    res2 = run_manifest(
        "advance",
        "--path", str(manifest_file),
        "--chapter", "1",
        "--section", "1",
        "--status", "completed",
    )
    assert res2.returncode == 0
    data2 = json.loads(res2.stdout)
    assert data2["course_status"] == "in_progress"  # sec 2 is still not_started, course is in_progress

    # Advance section 2 to completed -> all completed -> course completed
    res3 = run_manifest(
        "advance",
        "--path", str(manifest_file),
        "--chapter", "1",
        "--section", "2",
        "--status", "completed",
    )
    assert res3.returncode == 0
    data3 = json.loads(res3.stdout)
    assert data3["course_status"] == "completed"

    with open(manifest_file, "rb") as f:
        final_toml = tomllib.load(f)
    assert final_toml["course"]["status"] == "completed"
    assert final_toml["chapters"][0]["sections"][0]["status"] == "completed"
    assert final_toml["chapters"][0]["sections"][1]["status"] == "completed"


def test_advance_not_found(tmp_path: Path):
    """Verify advance returns error when chapter or section is absent."""
    course_dir = tmp_path / "course-not-found"
    manifest_file = course_dir / "course.toml"
    course_dir.mkdir(parents=True)
    manifest_file.write_text("""
[course]
slug = "test"
title = "Test"
status = "not_started"
created = "2026-10-10T00:00:00Z"
updated = "2026-10-10T00:00:00Z"
archetype = "applied_creation"

[[chapters]]
id = 1
slug = "ch-01"
title = "Chapter 1"
sections = []
""", encoding="utf-8")

    res = run_manifest(
        "advance",
        "--path", str(manifest_file),
        "--chapter", "1",
        "--section", "99",
        "--status", "in_progress",
    )
    assert res.returncode == 1
    err = json.loads(res.stderr)
    assert err["ok"] is False
    assert "not found" in err["error"]


def test_validate_success(tmp_path: Path):
    """Verify validate succeeds on compliant manifest."""
    manifest_file = tmp_path / "course.toml"
    manifest_file.write_text("""
[course]
slug = "valid-course"
title = "Valid Course"
status = "not_started"

[[chapters]]
id = 1
slug = "ch-01"
title = "Chapter 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Section 1"
status = "not_started"
""", encoding="utf-8")

    res = run_manifest("validate", "--path", str(manifest_file))
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["valid"] is True


def test_validate_schema_errors(tmp_path: Path):
    """Verify validate reports schema discrepancies."""
    manifest_file = tmp_path / "invalid_course.toml"
    manifest_file.write_text("""
[course]
slug = "missing-status-and-title"

[[chapters]]
# Missing id, slug, title
sections = [
  { id = 1, slug = "s1", title = "S1", status = "invalid_status" }
]
""", encoding="utf-8")

    res = run_manifest("validate", "--path", str(manifest_file))
    assert res.returncode == 1
    data = json.loads(res.stderr)
    assert data["ok"] is False
    assert data["valid"] is False
    assert any("title" in err for err in data["errors"])
    assert any("status" in err for err in data["errors"])


def test_validate_malformed_toml(tmp_path: Path):
    """Verify validate catches syntax errors in TOML."""
    manifest_file = tmp_path / "corrupted.toml"
    manifest_file.write_text("this is not = [valid toml", encoding="utf-8")

    res = run_manifest("validate", "--path", str(manifest_file))
    assert res.returncode == 1
    data = json.loads(res.stderr)
    assert data["ok"] is False
    assert "Invalid TOML" in data["error"]


def test_atomic_write_function(tmp_path: Path):
    """Verify atomic_write_toml creates file without leaving .tmp files behind."""
    sys.path.insert(0, str(MANIFEST_SCRIPT.parent))
    import manifest

    target_file = tmp_path / "nested" / "sub" / "test.toml"
    test_data = {"key": "value", "nested": {"number": 42}}

    manifest.atomic_write_toml(target_file, test_data)

    assert target_file.exists()
    temp_file = target_file.with_suffix(target_file.suffix + ".tmp")
    assert not temp_file.exists()

    with open(target_file, "rb") as f:
        loaded = tomllib.load(f)
    assert loaded == test_data
