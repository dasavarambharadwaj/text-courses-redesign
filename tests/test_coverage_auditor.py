"""tests/test_coverage_auditor.py — Test suite for Complete Coverage Verification Ledger (CAP-5)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from auditor import audit_coverage
from source_mapper import compile_source_map

AUDITOR_SCRIPT = SCRIPTS_DIR / "auditor.py"


@pytest.fixture
def coverage_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace with two source books and a matching course."""
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True)

    # 1. Raw sources
    raw_dir = ws / "research" / "distributed-consensus" / "sources" / "raw"
    raw_dir.mkdir(parents=True)

    # Source 1: Raft Paper
    raft_file = raw_dir / "raft.md"
    raft_content = """# In Search of an Understandable Consensus Algorithm
## 1. Introduction
Consensus algorithms allow a collection of machines to work as a coherent group.
## 2. Replicated State Machines
State machines on a collection of servers compute identical copies of the same state.
## 3. The Raft Consensus Algorithm
### Leader Election
Raft uses a heartbeat mechanism to trigger leader election.
### Log Replication
The leader accepts log entries from clients and replicates them.
"""
    raft_file.write_text(raft_content, encoding="utf-8")

    # Source 2: Paxos Notes
    paxos_file = raw_dir / "paxos.md"
    paxos_content = """# Paxos Made Simple
## Phase 1: Prepare and Promise
A proposer selects a proposal number n and sends a prepare request.
## Phase 2: Accept and Accepted
If a proposer receives a response to its prepare requests from a majority.
"""
    paxos_file.write_text(paxos_content, encoding="utf-8")

    # 2. Course directory
    course_dir = ws / "courses" / "distributed-consensus"
    course_dir.mkdir(parents=True)

    course_data = {
        "course": {
            "id": "distributed-consensus",
            "title": "Distributed Consensus Mastery",
            "archetype": "axiomatic_primitives",
        },
        "chapters": [
            {
                "id": "chapter-01",
                "title": "State Machines & Foundations",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "Introduction to Consensus",
                        "vocabulary_introduced": ["Consensus", "State Machines"],
                    },
                    {
                        "id": "sec-02",
                        "title": "Replicated State Machines",
                        "vocabulary_introduced": ["Replicated State Machines"],
                    },
                ],
            },
            {
                "id": "chapter-02",
                "title": "Consensus Protocols",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "Raft Leader Election and Replication",
                        "vocabulary_introduced": ["Leader Election", "Log Replication"],
                    },
                    {
                        "id": "sec-02",
                        "title": "Paxos Prepare and Accept Phases",
                        "vocabulary_introduced": ["Prepare and Promise", "Accept and Accepted"],
                    },
                ],
            },
        ],
    }

    import tomli_w
    (course_dir / "course.toml").write_text(tomli_w.dumps(course_data), encoding="utf-8")

    # Compile source-map.toml
    compile_source_map("distributed-consensus", workspace=ws)

    return ws


def test_audit_coverage_complete_pass(coverage_workspace: Path) -> None:
    """Verify that a fully mapped course achieves 100% coverage and emits a valid ledger."""
    ws = coverage_workspace
    res = audit_coverage("distributed-consensus", workspace=ws)

    assert res["ok"] is True
    assert res["status"] == "PASSED"
    assert res["dropped_sections"] == 0
    assert res["coverage_ratio"] == 100.0
    assert res["sources_audited"] == 2
    assert res["total_source_sections"] >= 4

    ledger_path = Path(res["ledger_path"])
    assert ledger_path.is_file()

    content = ledger_path.read_text(encoding="utf-8")
    assert "# Coverage Audit Ledger: Distributed Consensus Mastery" in content
    assert "Overall Coverage Ratio**: 100.0%" in content
    assert "Status**: PASSED" in content
    assert "[✓] Mapped" in content
    assert "[!] Dropped" not in content


def test_audit_coverage_detects_dropped_section(coverage_workspace: Path) -> None:
    """Verify that dropping a chapter from the syllabus causes coverage failure."""
    ws = coverage_workspace

    # Append an unmapped chapter to the source file
    raft_file = ws / "research" / "distributed-consensus" / "sources" / "raw" / "raft.md"
    raft_content = raft_file.read_text(encoding="utf-8")
    raft_content += "\n## 4. Cluster Membership Changes\nJoint consensus protocol for server reconfiguration.\n"
    raft_file.write_text(raft_content, encoding="utf-8")

    # Audit coverage without updating curriculum
    res = audit_coverage("distributed-consensus", workspace=ws)

    assert res["ok"] is False
    assert res["status"] == "FAILED"
    assert res["dropped_sections"] >= 1
    assert res["coverage_ratio"] < 100.0

    ledger_path = Path(res["ledger_path"])
    content = ledger_path.read_text(encoding="utf-8")
    assert "Status**: FAILED" in content
    assert "[!] Dropped" in content
    assert "Cluster Membership Changes" in content


def test_audit_coverage_cli(coverage_workspace: Path) -> None:
    """Verify auditor.py coverage CLI subcommand output and exit codes."""
    ws = coverage_workspace

    # Passing case (exit code 0)
    res_pass = subprocess.run(
        [sys.executable, str(AUDITOR_SCRIPT), "coverage", "--course", "distributed-consensus", "--workspace", str(ws)],
        capture_output=True,
        text=True,
    )
    assert res_pass.returncode == 0
    pass_data = json.loads(res_pass.stdout)
    assert pass_data["ok"] is True
    assert pass_data["status"] == "PASSED"

    # Failing case: add unmapped section
    paxos_file = ws / "research" / "distributed-consensus" / "sources" / "raw" / "paxos.md"
    paxos_content = paxos_file.read_text(encoding="utf-8") + "\n## Phase 3: Diskless Failover\nSpeculative crash recovery.\n"
    paxos_file.write_text(paxos_content, encoding="utf-8")

    res_fail = subprocess.run(
        [sys.executable, str(AUDITOR_SCRIPT), "coverage", "--course", "distributed-consensus", "--workspace", str(ws)],
        capture_output=True,
        text=True,
    )
    assert res_fail.returncode == 1
    fail_data = json.loads(res_fail.stdout or res_fail.stderr)
    assert fail_data["ok"] is False
    assert fail_data["status"] == "FAILED"


def test_zero_bmad_invariant() -> None:
    """Verify auditor.py contains strictly zero mentions of bmad."""
    content = AUDITOR_SCRIPT.read_text(encoding="utf-8").lower()
    assert "bmad" not in content, f"Found 'bmad' in {AUDITOR_SCRIPT}"
