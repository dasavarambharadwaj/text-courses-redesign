"""test_curriculum_brainstorm.py — Verification for FR-35 Autonomous Multi-Path Curriculum Brainstorming."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

COURSE_BUILDER_SCRIPT = Path("_tc/scripts/course_builder.py").resolve()


def test_autonomous_brainstorm_synthesis_and_scaffolding(tmp_path: Path):
    """Verify course builder generates 4 curricular paths and writes curriculum-brainstorm.md."""
    res = subprocess.run(
        [
            sys.executable,
            str(COURSE_BUILDER_SCRIPT),
            "create",
            "--slug",
            "kv-database",
            "--workspace",
            str(tmp_path),
            "--title",
            "Key-Value Storage Engine",
            "--topic",
            "LSM Trees and WAL storage engine",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["consensus_reached"] is True

    brainstorm_file = Path(data["brainstorm_path"])
    assert brainstorm_file.is_file()
    content = brainstorm_file.read_text(encoding="utf-8")

    # 1. Must contain all 4 archetypal learning paths
    assert "Foundational / First-Principles Architecture" in content
    assert "Hands-On / Project-First Architecture" in content
    assert "Problem-Driven / Diagnostic Architecture" in content
    assert "Intuitive / Metaphor-First Architecture" in content

    # 2. Must contain the Critical Hat Stress-Test Matrix
    assert "Universal Critical Hat Stress-Test Matrix" in content
    assert "Academic Purist" in content
    assert "Applied Practitioner" in content
    assert "Beginner Friction Hunter" in content
    assert "Edge-Case Systems Engineer" in content
    assert "Resource Tradeoff Optimizer" in content

    # 3. Must contain Faculty Triad synthesis verdict
    assert "Faculty Triad Consensus & Synthesized Hybrid" in content
    assert "Daedalus (Craftsman)" in content
    assert "Marie (Empirical)" in content
    assert "Hypatia (Pedagogue)" in content


def test_brainstorm_tailoring_to_learner_intent(tmp_path: Path):
    """Verify brainstorm hybrid adapts to learner profile (e.g. practical focus)."""
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "preferences.md").write_text(
        "practical_focus: true\nrole: Production Engineer\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            str(COURSE_BUILDER_SCRIPT),
            "create",
            "--slug",
            "raft-systems",
            "--workspace",
            str(tmp_path),
            "--title",
            "Raft Consensus",
            "--topic",
            "Leader election and log replication",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True

    brainstorm_file = Path(data["brainstorm_path"])
    content = brainstorm_file.read_text(encoding="utf-8")
    assert "Applied Production Craftsman Hybrid" in content
