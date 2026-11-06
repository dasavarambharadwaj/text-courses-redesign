#!/usr/bin/env python3
"""tests/test_four_hat_debate.py — Canonical 4-Hat Adversarial Research Debate & Decision Log tests (FR-30, FR-31, CAP-5)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

from _tc.scripts import scout


def test_conduct_four_hat_debate_protocol(tmp_path: Path) -> None:
    """Verify 4-hat dialectic debate conducts challenge rounds and writes debate.jsonl and debate-summary.md."""
    res = scout.conduct_four_hat_debate(
        slug="storage-engine",
        topic="Storage Engines and LSM Trees",
        workspace=tmp_path,
    )
    assert res["ok"] is True
    assert res["debate_records_count"] >= 3

    canon_jsonl = tmp_path / "_tc" / "research" / "storage-engine" / "debate.jsonl"
    canon_summary = tmp_path / "_tc" / "research" / "storage-engine" / "debate-summary.md"
    assert canon_jsonl.is_file(), "Canonical debate.jsonl missing from _tc/research/"
    assert canon_summary.is_file(), "Canonical debate-summary.md missing from _tc/research/"

    # Verify JSON Lines schema
    lines = [line.strip() for line in canon_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 3

    for line in lines:
        record = json.loads(line)
        assert "debate_id" in record
        assert "question" in record
        assert "hat_positions" in record
        assert "specialist_advice" in record
        assert "challenge_round" in record
        assert "resolution" in record
        assert "votes" in record

        # 4 Voting Hats
        positions = record["hat_positions"]
        assert "applied_practitioner" in positions
        assert "academic_purist" in positions
        assert "beginner_friction_hunter" in positions
        assert "edge_case_systems_engineer" in positions

        # 1 Non-Voting Specialist
        assert "ai_era_strategist" in record["specialist_advice"]

        # Challenge round exists
        assert len(record["challenge_round"]) >= 1
        for ch in record["challenge_round"]:
            assert "challenger" in ch
            assert "target" in ch
            assert "challenge" in ch
            assert "response" in ch

        # Resolution format
        res_data = record["resolution"]
        assert "decision" in res_data
        assert "rationale" in res_data
        assert res_data["confidence"] in {"high", "medium"}

    # Verify Summary Markdown
    summary_text = canon_summary.read_text(encoding="utf-8")
    assert "4-Hat Adversarial Research Debate & Decision Log" in summary_text
    assert "Hat 1: Industry Practitioner Hat" in summary_text
    assert "Hat 2: Academic Purist Hat" in summary_text
    assert "Hat 3: Beginner Friction Hunter Hat" in summary_text
    assert "Hat 4: Edge-Case Systems Engineer Hat" in summary_text
    assert "Round 1: Initial Archetypal Stances" in summary_text
    assert "Round 2: Adversarial Challenge & Cross-Examination" in summary_text
    assert "Final Resolution & Consensus Decision" in summary_text


def test_scout_run_generates_debate_artifacts(tmp_path: Path) -> None:
    """Verify scout.run_scout conducts the 4-hat debate automatically and populates digest."""
    res = scout.run_scout(
        slug="paxos-consensus",
        topic="Paxos Consensus Algorithm",
        workspace=tmp_path,
    )
    assert res["ok"] is True
    assert res.get("debate_records_count", 0) >= 3
    assert "debate_file" in res
    assert Path(res["debate_file"]).is_file()

    # Test cache getters
    records = scout.get_cached_debate("paxos-consensus", workspace=tmp_path)
    assert len(records) >= 3

    summary = scout.get_cached_debate_summary("paxos-consensus", workspace=tmp_path)
    assert "4-Hat Adversarial Research Debate" in summary


def test_scout_cli_debate_subcommand(tmp_path: Path) -> None:
    """Verify CLI scout.py debate subcommand outputs summary and JSON records."""
    # Run debate generation via CLI
    cmd_gen = [
        sys.executable,
        str(Path(scout.__file__).resolve()),
        "debate",
        "--slug",
        "cli-debate",
        "--topic",
        "Memory Allocators in Rust",
        "--workspace",
        str(tmp_path),
        "--json",
    ]
    res_gen = subprocess.run(cmd_gen, capture_output=True, text=True)
    assert res_gen.returncode == 0
    data = json.loads(res_gen.stdout)
    assert data["ok"] is True
    assert data["debate_records_count"] >= 3

    # Retrieve cached debate via CLI
    cmd_get = [
        sys.executable,
        str(Path(scout.__file__).resolve()),
        "debate",
        "--slug",
        "cli-debate",
        "--workspace",
        str(tmp_path),
        "--json",
    ]
    res_get = subprocess.run(cmd_get, capture_output=True, text=True)
    assert res_get.returncode == 0
    cached = json.loads(res_get.stdout)
    assert cached["ok"] is True
    assert len(cached["records"]) >= 3
