"""tests/test_practical_evaluator.py — Test suite for Practical Project Verification Engine."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path
import pytest
import tomli_w

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "_tc" / "scripts" / "practical_evaluator.py"
SKILL_PATH = Path(__file__).resolve().parent.parent / "skills" / "tc-practicals" / "SKILL.md"


@pytest.fixture
def temp_course_tree(tmp_path: Path) -> Path:
    """Create a temporary course tree for practical evaluations."""
    course_dir = tmp_path / "courses" / "distributed-kv"
    course_dir.mkdir(parents=True)

    manifest_data = {
        "course": {
            "title": "Distributed KV Store",
            "slug": "distributed-kv",
            "version": "1.0.0",
            "status": "in-progress",
            "archetype": "systems",
        },
        "chapter": [
            {
                "title": "Replication and Consensus",
                "slug": "01-replication",
                "status": "in-progress",
                "section": [
                    {
                        "title": "Raft Consensus Core",
                        "slug": "01-raft",
                        "status": "completed",
                    }
                ],
            }
        ],
    }

    with open(course_dir / "course.toml", "wb") as f:
        tomli_w.dump(manifest_data, f)

    return course_dir


def test_init_brief_default_generation(temp_course_tree: Path) -> None:
    """Verify default project brief initialization in portfolio/project-01/."""
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "init-brief",
        "--course",
        str(temp_course_tree),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["project_id"] == "01"
    assert data["complexity"] == "medium"

    spec_path = Path(data["spec_path"])
    assert spec_path.is_file()
    content = spec_path.read_text(encoding="utf-8")
    assert "Applied Capstone: Distributed KV Store" in content
    assert "status: \"pending\"" in content
    assert "Lens 1: Functional Completeness" in content
    assert "Lens 4: Verification Integrity" in content


def test_init_brief_weighted_by_misconceptions(temp_course_tree: Path) -> None:
    """Verify that project brief explicitly incorporates past misconceptions from test-ledger.jsonl."""
    # Write a test-ledger.jsonl with diagnosed misconceptions
    ledger_path = temp_course_tree / "test-ledger.jsonl"
    records = [
        {
            "timestamp": "2026-10-10T20:00:00Z",
            "course": "distributed-kv",
            "chapter": "01-replication",
            "section": "01-raft",
            "question_type": "hinge_scenario",
            "prompt": "Split brain scenario",
            "learner_response": "Accept both writes",
            "outcome": "fail",
            "diagnosed_misconception": "CONFUSION_SPLIT_BRAIN_QUORUM",
            "remediation_summary": "Quorum must be strictly majority",
            "confidence_level": "high",
        },
        {
            "timestamp": "2026-10-10T20:15:00Z",
            "course": "distributed-kv",
            "chapter": "01-replication",
            "section": "01-raft",
            "question_type": "hinge_scenario",
            "prompt": "Heartbeat timeout election",
            "learner_response": "Elect immediately without timeout randomization",
            "outcome": "fail",
            "diagnosed_misconception": "CONFUSION_ELECTION_TIMEOUT_JITTER",
            "remediation_summary": "Randomize timeouts to prevent split votes",
            "confidence_level": "high",
        },
    ]
    with open(ledger_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "init-brief",
        "--course",
        str(temp_course_tree),
        "--project-id",
        "02",
        "--custom-idea",
        "Build a 3-node in-memory Raft cluster",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["project_id"] == "02"
    assert "CONFUSION_SPLIT_BRAIN_QUORUM" in data["misconceptions_addressed"]
    assert "CONFUSION_ELECTION_TIMEOUT_JITTER" in data["misconceptions_addressed"]

    spec_path = Path(data["spec_path"])
    content = spec_path.read_text(encoding="utf-8")
    assert "CONFUSION_SPLIT_BRAIN_QUORUM" in content
    assert "CONFUSION_ELECTION_TIMEOUT_JITTER" in content
    assert "Build a 3-node in-memory Raft cluster" in content


def test_review_pass_updates_spec_and_course_toml(temp_course_tree: Path) -> None:
    """Passing a project review updates review-report.md, spec status, and marks course.toml completed."""
    # First init brief
    subprocess.run([
        sys.executable,
        str(SCRIPT_PATH),
        "init-brief",
        "--course",
        str(temp_course_tree),
        "--project-id",
        "01",
    ], check=True)

    # Now run review pass
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "review",
        "--course",
        str(temp_course_tree),
        "--project-id",
        "01",
        "--verdict",
        "PASS",
        "--functional-lens",
        "KV node handles GET/PUT with leader election.",
        "--edge-lens",
        "Network partition handled properly via term updates.",
        "--architecture-lens",
        "Zero external framework dependencies, clean separation.",
        "--verification-lens",
        "12/12 unit and integration tests passing.",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["verdict"] == "PASS"
    assert data["course_completed"] is True

    # Check review report file
    report_path = Path(data["report_path"])
    assert report_path.is_file()
    report_text = report_path.read_text(encoding="utf-8")
    assert "Overall Verdict:** PASS" in report_text
    assert "KV node handles GET/PUT" in report_text
    assert "12/12 unit and integration tests passing." in report_text

    # Check project-spec.md was updated to approved
    spec_path = temp_course_tree / "portfolio" / "project-01" / "project-spec.md"
    assert 'status: "approved"' in spec_path.read_text(encoding="utf-8")

    # Check course.toml status is completed
    with open(temp_course_tree / "course.toml", "rb") as f:
        manifest = tomllib.load(f)
    assert manifest["course"]["status"] == "completed"


def test_review_needs_work_leaves_course_in_progress(temp_course_tree: Path) -> None:
    """Needs work verdict creates remediation report and leaves course in-progress."""
    subprocess.run([
        sys.executable,
        str(SCRIPT_PATH),
        "init-brief",
        "--course",
        str(temp_course_tree),
        "--project-id",
        "01",
    ], check=True)

    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "review",
        "--course",
        str(temp_course_tree),
        "--project-id",
        "01",
        "--verdict",
        "NEEDS_WORK",
        "--functional-lens",
        "Missing log compaction endpoint.",
        "--edge-lens",
        "Node crashes on socket disconnect.",
        "--remediation",
        "Implement snapshotting and add socket disconnect error recovery.",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["verdict"] == "NEEDS_WORK"
    assert data["course_completed"] is False

    report_path = Path(data["report_path"])
    report_text = report_path.read_text(encoding="utf-8")
    assert "Overall Verdict:** NEEDS_WORK" in report_text
    assert "Implement snapshotting" in report_text

    # Check spec status is needs_work
    spec_path = temp_course_tree / "portfolio" / "project-01" / "project-spec.md"
    assert 'status: "needs_work"' in spec_path.read_text(encoding="utf-8")

    # Check course.toml is still in-progress
    with open(temp_course_tree / "course.toml", "rb") as f:
        manifest = tomllib.load(f)
    assert manifest["course"]["status"] == "in-progress"


def test_zero_bmad_references() -> None:
    """Verify strict absence of BMad leakage in practical evaluator script and skill."""
    forbidden = ["bmad", "b-mad", "b_mad", "BMAD", "Bmad"]
    script_content = SCRIPT_PATH.read_text(encoding="utf-8")
    skill_content = SKILL_PATH.read_text(encoding="utf-8")

    for word in forbidden:
        assert word not in script_content, f"Found '{word}' in {SCRIPT_PATH}"
        assert word not in skill_content, f"Found '{word}' in {SKILL_PATH}"
