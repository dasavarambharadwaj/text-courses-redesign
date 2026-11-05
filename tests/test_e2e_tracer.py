"""test_e2e_tracer.py — Comprehensive vertical tracer for TextCourses framework.

Executes the complete vertical tracer sequence through the unified dispatcher `tc.py`:
1. tc init: Scaffold workspace & profile
2. tc research / scout: Gather topic intelligence
3. tc index: Build potato-proof SQLite FTS5 RAG database
4. tc create: Autonomous multi-path brainstorm & course scaffolding
5. tc teach: Socratic session & note compilation
6. tc practicals: In-loop lab evaluation
7. tc test: Diagnostic conceptual assessment & ledger tracking
8. tc dag / roadmap: Prerequisite verification
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "_tc" / "scripts"
TC_CLI = SCRIPTS_DIR / "tc.py"


def run_tc(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the unified tc.py dispatcher CLI."""
    cmd = [sys.executable, str(TC_CLI), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def extract_json(output: str) -> dict:
    """Extract JSON object from stdout that may include diagnostic console banners."""
    idx = output.find("{")
    last_idx = output.rfind("}")
    if idx != -1 and last_idx != -1:
        return json.loads(output[idx : last_idx + 1])
    return json.loads(output)


def test_complete_vertical_tracer(tmp_path: Path):
    """Verify clean vertical tracer across all 8 pipeline milestones."""
    workspace = tmp_path / "tracer_workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    # 1. tc init
    res_init = run_tc("init", "--workspace", str(workspace), "--json")
    assert res_init.returncode == 0, res_init.stderr
    init_data = extract_json(res_init.stdout)
    assert init_data["ok"] is True
    assert (workspace / "profile" / "preferences.md").is_file()
    assert (workspace / "profile" / "memlog.md").is_file()

    # 2. Add sample research material and run indexer
    research_dir = workspace / "research" / "distributed-raft" / "sources"
    research_dir.mkdir(parents=True, exist_ok=True)
    sample_spec = research_dir / "raft_paper.md"
    sample_spec.write_text(
        "# In Search of an Understandable Consensus Algorithm\n\n"
        "Raft is a consensus algorithm for managing a replicated log.\n"
        "Leader election is the first phase of Raft consensus.\n"
        "State machine safety ensures that if a server applies an entry, no other server will.\n",
        encoding="utf-8",
    )

    # 3. tc index
    res_index = run_tc(
        "index",
        "--slug", "distributed-raft",
        "--workspace", str(workspace),
        "--json",
    )
    assert res_index.returncode == 0, res_index.stderr
    idx_data = extract_json(res_index.stdout)
    assert idx_data["ok"] is True
    assert idx_data["total_chunks"] > 0
    rag_db = workspace / "research" / "distributed-raft" / "rag-db" / "index.db"
    assert rag_db.is_file()

    # 4. tc create
    res_create = run_tc(
        "create",
        "--slug", "distributed-raft",
        "--title", "Distributed Consensus with Raft",
        "--workspace", str(workspace),
        "--json",
    )
    assert res_create.returncode == 0, res_create.stderr
    create_data = extract_json(res_create.stdout)
    assert create_data["ok"] is True
    course_dir = workspace / "courses" / "distributed-raft"
    course_manifest = (course_dir / ".tc" / "course.toml") if (course_dir / ".tc" / "course.toml").is_file() else (course_dir / "course.toml")
    assert course_manifest.is_file()

    # 5. tc teach session
    res_teach = run_tc(
        "teach",
        "session",
        "--course", "distributed-raft",
        "--workspace", str(workspace),
        "--json",
    )
    assert res_teach.returncode == 0, res_teach.stderr
    teach_data = extract_json(res_teach.stdout)
    assert teach_data["ok"] is True
    active_sec = teach_data["active_section"]
    sec_dir = Path(active_sec["section_dir"])
    lp_file = sec_dir / "lesson-plan.md"
    assert lp_file.is_file()

    # Advance until last concept
    lp_content = lp_file.read_text(encoding="utf-8")
    unchecked = re.findall(r"^-\s*\[\s*\]\s+(.+)$", lp_content, re.MULTILINE)
    for _ in range(max(0, len(unchecked) - 1)):
        adv_res = run_tc(
            "teach",
            "advance",
            "--course", "distributed-raft",
            "--workspace", str(workspace),
            "--json",
        )
        assert adv_res.returncode == 0, adv_res.stderr

    # Advance section to completion with recap
    res_adv = run_tc(
        "teach",
        "advance",
        "--course", "distributed-raft",
        "--workspace", str(workspace),
        "--recap",
        "Leader election maintains high availability.",
        "Log replication ensures state machine consistency.",
        "Heartbeats prevent split-brain elections.",
        "--json",
    )
    assert res_adv.returncode == 0, res_adv.stderr
    adv_data = extract_json(res_adv.stdout)
    assert adv_data["ok"] is True
    assert adv_data["section_fully_completed"] is True

    # 6. tc test prepare & record
    res_prep = run_tc(
        "test",
        "prepare",
        "--course", str(course_dir),
    )
    assert res_prep.returncode == 0, res_prep.stderr
    prep_data = extract_json(res_prep.stdout)
    assert prep_data["ok"] is True

    res_record = run_tc(
        "test",
        "record",
        "--course", str(course_dir),
        "--chapter", active_sec["chapter_id"],
        "--section", active_sec["section_id"],
        "--type", "hinge_scenario",
        "--prompt", "Why does Raft require a majority quorum for leader election?",
        "--response", "Any two quorums must overlap on at least one server that has the most up-to-date log.",
        "--outcome", "pass",
    )
    assert res_record.returncode == 0, res_record.stderr
    rec_data = extract_json(res_record.stdout)
    assert rec_data["ok"] is True
    assert rec_data["section_status_updated"] is True

    # 7. tc practicals init-brief & review
    res_brief = run_tc(
        "practicals",
        "init-brief",
        "--course", str(course_dir),
        "--project-id", "01",
    )
    assert res_brief.returncode == 0, res_brief.stderr
    brief_data = extract_json(res_brief.stdout)
    assert brief_data["ok"] is True

    res_review = run_tc(
        "practicals",
        "review",
        "--course", str(course_dir),
        "--project-id", "01",
        "--verdict", "PASS",
        "--functional-lens", "Full leader election and log replication passing.",
        "--edge-lens", "Partitions and dropped RPC packets handled correctly.",
        "--architecture-lens", "Clean state machine implementation.",
        "--verification-lens", "Deterministic simulation tests pass.",
    )
    assert res_review.returncode == 0, res_review.stderr
    rev_data = extract_json(res_review.stdout)
    assert rev_data["ok"] is True
    assert rev_data["verdict"] == "PASS"

    # 8. Check DAG / course completion status
    with open(course_manifest, "rb") as f:
        manifest_data = tomllib.load(f)
    assert manifest_data["course"]["status"] == "completed"
