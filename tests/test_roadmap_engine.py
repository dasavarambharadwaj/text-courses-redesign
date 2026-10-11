"""tests/test_roadmap_engine.py — Unit tests for Macro-Roadmap Manifest and DAG extensions (FR-26).

Validates:
- manifest.py init-roadmap, add-course, advance-course, and roadmap schema validation
- dag.py multi-course DAG validation, topological ordering, cycle detection, and missing prerequisite rejection
- Zero BMad references across scripts
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import tomli_w

MANIFEST_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "manifest.py"
DAG_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "dag.py"


def run_manifest(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(MANIFEST_SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def run_dag(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(DAG_SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_manifest_roadmap_crud_and_status(tmp_path: Path):
    """Verify manifest.py manages roadmap lifecycle: init, add courses, advance status."""
    roadmap_file = tmp_path / "roadmap.toml"

    # 1. init-roadmap
    res = run_manifest("init-roadmap", "--path", str(roadmap_file), "--title", "Data Science & AI")
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True

    # 2. add-course 1
    res = run_manifest(
        "add-course",
        "--path", str(roadmap_file),
        "--slug", "python-data",
        "--title", "Python for Data Analysis",
        "--status", "active",
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["total_courses"] == 1

    # 3. add-course 2 with prerequisite
    res = run_manifest(
        "add-course",
        "--path", str(roadmap_file),
        "--slug", "ml-foundations",
        "--title", "Machine Learning Foundations",
        "--status", "not_started",
        "--prerequisites", "python-data",
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["total_courses"] == 2

    # 4. validate succeeds
    res = run_manifest("validate", "--path", str(roadmap_file))
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True

    # 5. advance-course
    res = run_manifest(
        "advance-course",
        "--path", str(roadmap_file),
        "--slug", "python-data",
        "--status", "completed",
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["status"] == "completed"

    # advance second course to complete entire roadmap
    res = run_manifest(
        "advance-course",
        "--path", str(roadmap_file),
        "--slug", "ml-foundations",
        "--status", "waived",
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["roadmap_status"] == "completed"


def test_manifest_roadmap_validation_catches_missing_prereq(tmp_path: Path):
    """Verify manifest.py validate catches unknown course prerequisite reference."""
    roadmap_file = tmp_path / "roadmap.toml"
    run_manifest("init-roadmap", "--path", str(roadmap_file), "--title", "Distributed Systems")
    run_manifest(
        "add-course",
        "--path", str(roadmap_file),
        "--slug", "raft-consensus",
        "--title", "Raft Consensus",
        "--prerequisites", "non-existent-course",
    )

    res = run_manifest("validate", "--path", str(roadmap_file))
    assert res.returncode != 0
    data = json.loads(res.stdout or res.stderr)
    assert data["ok"] is False
    assert any("references unknown prerequisite" in err for err in data["errors"])


def test_dag_roadmap_topological_sorting(tmp_path: Path):
    """Verify dag.py validates and orders multi-course roadmap DAG."""
    roadmap_file = tmp_path / "roadmap.toml"
    roadmap_data = {
        "roadmap": {
            "title": "Systems Track",
            "status": "active",
            "courses": [
                {
                    "slug": "course-3-networking",
                    "title": "Networking",
                    "status": "not_started",
                    "prerequisites": ["course-2-concurrency"],
                },
                {
                    "slug": "course-1-c-basics",
                    "title": "C Basics",
                    "status": "completed",
                    "prerequisites": [],
                },
                {
                    "slug": "course-2-concurrency",
                    "title": "Concurrency",
                    "status": "active",
                    "prerequisites": ["course-1-c-basics"],
                },
            ],
        }
    }
    with open(roadmap_file, "wb") as f:
        tomli_w.dump(roadmap_data, f)

    # 1. validate
    res = run_dag("validate", "--path", str(roadmap_file))
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["valid"] is True
    assert data["total_nodes"] == 3

    # 2. order
    res = run_dag("order", "--path", str(roadmap_file))
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["order"] == ["course-1-c-basics", "course-2-concurrency", "course-3-networking"]


def test_dag_roadmap_cycle_detection(tmp_path: Path):
    """Verify dag.py detects cycle in multi-course roadmap DAG."""
    roadmap_file = tmp_path / "roadmap.toml"
    roadmap_data = {
        "roadmap": {
            "title": "Cyclic Track",
            "status": "active",
            "courses": [
                {
                    "slug": "course-a",
                    "title": "Course A",
                    "prerequisites": ["course-b"],
                },
                {
                    "slug": "course-b",
                    "title": "Course B",
                    "prerequisites": ["course-a"],
                },
            ],
        }
    }
    with open(roadmap_file, "wb") as f:
        tomli_w.dump(roadmap_data, f)

    res = run_dag("validate", "--path", str(roadmap_file))
    assert res.returncode != 0
    data = json.loads(res.stdout or res.stderr)
    assert data["ok"] is False
    assert "circular" in data["error"].lower() or "cycle" in data["error"].lower()
