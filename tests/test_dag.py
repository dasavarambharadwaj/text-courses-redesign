"""test_dag.py — Unit tests for TextCourses DAG validator (dag.py).

Verifies cycle detection via graphlib.TopologicalSorter, topological ordering,
missing prerequisite rejection, and schema resilience across curriculum graphs (AD-4, FR-7, FR-8).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

DAG_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "dag.py"


def run_dag(*args: str) -> subprocess.CompletedProcess[str]:
    """Helper to run dag.py CLI and capture stdout/stderr."""
    cmd = [sys.executable, str(DAG_SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_dag_help():
    """Verify help subcommand displays usage and available subcommands."""
    result = run_dag("--help")
    assert result.returncode == 0
    assert "TextCourses deterministic prerequisite DAG validator" in result.stdout
    assert "validate" in result.stdout
    assert "order" in result.stdout


def test_validate_valid_dag_sections(tmp_path: Path):
    """Verify valid sequential section prerequisites are topologically ordered."""
    manifest_file = tmp_path / "course.toml"
    content = """
[course]
slug = "rust-basics"
title = "Rust Basics"
status = "not_started"

[[chapters]]
id = 1
slug = "ch-01"
title = "Chapter 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Variables"
prerequisites = []

[[chapters.sections]]
id = 2
slug = "sec-02"
title = "Ownership"
prerequisites = [1]

[[chapters.sections]]
id = 3
slug = "sec-03"
title = "Borrowing"
prerequisites = [2]
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_dag("validate", "--path", str(manifest_file))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["valid"] is True
    assert data["order"] == [1, 2, 3]
    assert data["total_nodes"] == 3


def test_validate_valid_dag_slugs(tmp_path: Path):
    """Verify valid prerequisite graph using slug strings."""
    manifest_file = tmp_path / "course.toml"
    content = """
[course]
slug = "systems-foundations"
title = "Systems Foundations"
status = "not_started"

[[chapters]]
id = 1
slug = "ch-foundations"
title = "Foundations"

[[chapters.sections]]
id = 1
slug = "intro"
title = "Introduction"
prerequisites = []

[[chapters.sections]]
id = 2
slug = "memory"
title = "Memory Model"
prerequisites = ["intro"]

[[chapters.sections]]
id = 3
slug = "concurrency"
title = "Concurrency"
prerequisites = ["memory"]
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_dag("validate", "--path", str(manifest_file))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["valid"] is True
    assert data["order"] == ["intro", "memory", "concurrency"]


def test_validate_diamond_dag(tmp_path: Path):
    """Verify diamond DAG where D depends on B and C, which both depend on A."""
    manifest_file = tmp_path / "course.toml"
    content = """
[course]
slug = "diamond-course"
title = "Diamond Course"
status = "not_started"

[[chapters]]
id = 1
slug = "ch-01"
title = "Chapter 1"

[[chapters.sections]]
id = 1
slug = "sec-a"
title = "A"
prerequisites = []

[[chapters.sections]]
id = 2
slug = "sec-b"
title = "B"
prerequisites = [1]

[[chapters.sections]]
id = 3
slug = "sec-c"
title = "C"
prerequisites = [1]

[[chapters.sections]]
id = 4
slug = "sec-d"
title = "D"
prerequisites = [2, 3]
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_dag("validate", "--path", str(manifest_file))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["valid"] is True
    order = data["order"]
    assert order[0] == 1
    assert order[-1] == 4
    assert set(order[1:3]) == {2, 3}


def test_validate_chapter_level_dag(tmp_path: Path):
    """Verify topological validation works at chapter level when chapters have prerequisites."""
    manifest_file = tmp_path / "course.toml"
    content = """
[course]
slug = "track-curriculum"
title = "Track Curriculum"
status = "not_started"

[[chapters]]
id = 1
slug = "ch-01-intro"
title = "Intro"
prerequisites = []

[[chapters]]
id = 2
slug = "ch-02-core"
title = "Core"
prerequisites = [1]

[[chapters]]
id = 3
slug = "ch-03-advanced"
title = "Advanced"
prerequisites = [2]
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_dag("validate", "--path", str(manifest_file))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["order"] == [1, 2, 3]


def test_validate_direct_dag_table(tmp_path: Path):
    """Verify top-level [dag] or [prerequisites] table is properly sorted."""
    manifest_file = tmp_path / "course.toml"
    content = """
[course]
slug = "custom-dag"
title = "Custom DAG"
status = "not_started"

[prerequisites]
"compile" = ["parse"]
"parse" = ["lex"]
"optimize" = ["compile"]
"lex" = []
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_dag("validate", "--path", str(manifest_file))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["order"] == ["lex", "parse", "compile", "optimize"]


def test_order_subcommand(tmp_path: Path):
    """Verify order subcommand outputs clean order array and path."""
    manifest_file = tmp_path / "course.toml"
    content = """
[course]
slug = "order-test"
title = "Order Test"
status = "not_started"

[[chapters]]
id = 1
slug = "ch-01"
title = "Ch 1"

[[chapters.sections]]
id = 10
slug = "s10"
title = "S10"

[[chapters.sections]]
id = 20
slug = "s20"
title = "S20"
prerequisites = [10]
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_dag("order", "--path", str(manifest_file))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["order"] == [10, 20]
    assert data["total_nodes"] == 2


def test_detect_dependency_cycle_direct(tmp_path: Path):
    """Verify direct circular dependency (1 -> 2 -> 1) is caught and reported."""
    manifest_file = tmp_path / "course.toml"
    content = """
[course]
slug = "cyclic-course"
title = "Cyclic Course"
status = "not_started"

[[chapters]]
id = 1
slug = "ch-01"
title = "Ch 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Sec 1"
prerequisites = [2]

[[chapters.sections]]
id = 2
slug = "sec-02"
title = "Sec 2"
prerequisites = [1]
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_dag("validate", "--path", str(manifest_file))
    assert result.returncode == 1
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert "Circular dependency detected" in err_data["error"]
    assert "cycle" in err_data
    assert len(err_data["cycle"]) >= 2
    assert set(err_data["cycle"]) == {1, 2}


def test_detect_dependency_cycle_indirect(tmp_path: Path):
    """Verify 3-node cycle (A -> B -> C -> A) is caught and reported."""
    manifest_file = tmp_path / "course.toml"
    content = """
[course]
slug = "indirect-cycle"
title = "Indirect Cycle"
status = "not_started"

[[chapters]]
id = 1
slug = "ch-01"
title = "Ch 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Sec 1"
prerequisites = [3]

[[chapters.sections]]
id = 2
slug = "sec-02"
title = "Sec 2"
prerequisites = [1]

[[chapters.sections]]
id = 3
slug = "sec-03"
title = "Sec 3"
prerequisites = [2]
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_dag("validate", "--path", str(manifest_file))
    assert result.returncode == 1
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert "Circular dependency detected" in err_data["error"]
    assert set(err_data["cycle"]) == {1, 2, 3}


def test_detect_self_cycle(tmp_path: Path):
    """Verify self-referential cycle (A -> A) is caught and reported."""
    manifest_file = tmp_path / "course.toml"
    content = """
[course]
slug = "self-cycle"
title = "Self Cycle"
status = "not_started"

[[chapters]]
id = 1
slug = "ch-01"
title = "Ch 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Sec 1"
prerequisites = [1]
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_dag("validate", "--path", str(manifest_file))
    assert result.returncode == 1
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert "Circular dependency detected" in err_data["error"]
    assert 1 in err_data["cycle"]


def test_detect_missing_prerequisite_section(tmp_path: Path):
    """Verify reference to nonexistent section ID is rejected with antecedent ID."""
    manifest_file = tmp_path / "course.toml"
    content = """
[course]
slug = "missing-prereq"
title = "Missing Prereq"
status = "not_started"

[[chapters]]
id = 1
slug = "ch-01"
title = "Ch 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Sec 1"
prerequisites = [99]
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_dag("validate", "--path", str(manifest_file))
    assert result.returncode == 1
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert "Missing prerequisite" in err_data["error"]
    assert "99" in str(err_data["missing"])


def test_detect_missing_prerequisite_chapter(tmp_path: Path):
    """Verify reference to nonexistent chapter ID is rejected with antecedent ID."""
    manifest_file = tmp_path / "course.toml"
    content = """
[course]
slug = "missing-chapter-prereq"
title = "Missing Chapter Prereq"
status = "not_started"

[[chapters]]
id = 1
slug = "ch-01"
title = "Ch 1"
prerequisites = ["nonexistent-chapter"]
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_dag("validate", "--path", str(manifest_file))
    assert result.returncode == 1
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert "Missing prerequisite" in err_data["error"]
    assert "nonexistent-chapter" in str(err_data["missing"])


def test_missing_manifest_file(tmp_path: Path):
    """Verify missing manifest path returns clean JSON error and exit 1."""
    nonexistent = tmp_path / "does_not_exist.toml"
    result = run_dag("validate", "--path", str(nonexistent))
    assert result.returncode == 1
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert "Manifest not found" in err_data["error"]


def test_malformed_toml(tmp_path: Path):
    """Verify malformed TOML returns clean JSON error and exit 1."""
    manifest_file = tmp_path / "broken.toml"
    manifest_file.write_text("invalid = [toml unclosed", encoding="utf-8")

    result = run_dag("validate", "--path", str(manifest_file))
    assert result.returncode == 1
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert "Malformed TOML" in err_data["error"]


def test_directory_path_resolution(tmp_path: Path):
    """Verify passing a directory path resolves course.toml automatically."""
    manifest_file = tmp_path / "course.toml"
    content = """
[course]
slug = "dir-test"
title = "Dir Test"
status = "not_started"

[[chapters]]
id = 1
slug = "ch-01"
title = "Ch 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Sec 1"
"""
    manifest_file.write_text(content.strip(), encoding="utf-8")

    result = run_dag("validate", "--path", str(tmp_path))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["valid"] is True
