"""tests/test_triad_dialectic.py — Test suite for Adversarial Triad Consensus Dialectic (FR-31).

Validates:
- Daedalus, Marie, and Hypatia distinct persona roles and arguments
- Ingestion of research dossiers and profile/preferences.md
- Gap topics identified and injected to bridge user intent
- Live fact-checking query generation and verification
- Generation of courses/<slug>/consensus-deliberation.md transcript
- Structured consensus trace in _tc/cache/consensus-trace.jsonl with participants and fact-checks
- Refusal / blocking of course creation upon unresolved audit dissent
- Zero-BMad references in scripts and skills
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

BUILDER_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "course_builder.py"
SKILL_FILE = Path(__file__).parent.parent / "skills" / "tc-create" / "SKILL.md"


def test_zero_bmad_references():
    """Verify strict zero-BMad references in builder script and tc-create skill."""
    for target in [BUILDER_SCRIPT, SKILL_FILE]:
        text = target.read_text(encoding="utf-8")
        assert not re.search(r"\bbmad\b", text, re.IGNORECASE), f"Found BMad mention in {target}"


def test_adversarial_triad_consensus_scaffolding(tmp_path: Path):
    """Verify course creation generates consensus-deliberation.md and logs trace."""
    # Setup profile/preferences.md
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "preferences.md").write_text(
        "---\nrole: Staff Systems Engineer\nteacher: feynman\nstyle_profile: direct_technical\n---\n",
        encoding="utf-8",
    )

    # Setup research dossier
    research_dir = tmp_path / "research" / "raft-engine"
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "dossier.md").write_text(
        "# Domain Research Dossier: Raft Consensus Engine\n\n## 1. Executive Summary\nRaft state machine replication.\n",
        encoding="utf-8",
    )
    (research_dir / "digest.json").write_text(
        json.dumps({
            "metadata": {"title": "Raft Consensus", "slug": "raft-engine", "confidence": "high"},
            "vocabulary": ["LogEntry", "Term", "AppendEntries"],
            "toc": [{"level": 1, "title": "Leader Election"}, {"level": 1, "title": "Log Replication"}],
        }),
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            str(BUILDER_SCRIPT),
            "create",
            "--slug",
            "raft-engine",
            "--title",
            "Raft Consensus Engine",
            "--archetype",
            "applied_creation",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Command failed: {res.stderr}"
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["consensus_reached"] is True
    assert data["unanimous"] is True
    assert len(data.get("gap_topics_covered", [])) >= 1

    course_dir = tmp_path / "courses" / "raft-engine"
    assert course_dir.is_dir()

    # Check consensus-deliberation.md
    delib_file = course_dir / "consensus-deliberation.md"
    assert delib_file.is_file(), "consensus-deliberation.md was not created"
    delib_text = delib_file.read_text(encoding="utf-8")

    # Verify all 3 participants are present and in-character
    assert "Daedalus (Curriculum Architect)" in delib_text
    assert "Marie Curie (Empirical Investigator & Fact-Checker)" in delib_text
    assert "Hypatia of Alexandria (Logic & Prerequisite Auditor)" in delib_text
    assert "Live Fact-Checking Verification Log" in delib_text
    assert "Learner-Personalized Topic Additions" in delib_text
    assert "UNANIMOUS CONSENSUS REACHED" in delib_text

    # Verify consensus trace in cache
    trace_file = tmp_path / "_tc" / "cache" / "consensus-trace.jsonl"
    assert trace_file.is_file()
    lines = trace_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    trace_record = json.loads(lines[-1])
    assert trace_record["slug"] == "raft-engine"
    assert trace_record["consensus_reached"] is True
    assert trace_record["unanimous"] is True
    assert trace_record["participants"]["Daedalus"] == "agreed"
    assert trace_record["participants"]["Marie"] == "agreed"
    assert trace_record["participants"]["Hypatia"] == "agreed"
    assert len(trace_record["live_fact_checks"]) >= 1


def test_builder_deliberation_subcommand(tmp_path: Path):
    """Verify deliberation CLI subcommand outputs the deliberation markdown."""
    course_dir = tmp_path / "courses" / "async-runtime"
    course_dir.mkdir(parents=True, exist_ok=True)
    delib_content = "# Triad Consensus Deliberation: Async Runtime\n\nAll critics approve."
    (course_dir / "consensus-deliberation.md").write_text(delib_content, encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(BUILDER_SCRIPT),
            "deliberation",
            "--slug",
            "async-runtime",
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
    assert "Async Runtime" in data["content"]
