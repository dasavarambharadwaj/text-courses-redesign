"""tests/test_unified_tc.py — Verification of Unified /tc Skill & State Machine (CAP-1, CAP-6)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from tc import dispatch_conversational_turn
from course_builder import create_course


def init_learner_profile(workspace: Path) -> Path:
    """Helper to initialize profile/preferences.md."""
    pref_file = workspace / "profile" / "preferences.md"
    pref_file.parent.mkdir(parents=True, exist_ok=True)
    pref_file.write_text(
        "role: Distributed Systems Engineer\ncompetency_level: intermediate\npractical_focus: true\n",
        encoding="utf-8",
    )
    return pref_file


def test_dispatch_fresh_workspace_intake_needed(tmp_path: Path):
    """Verify fresh uninitialized workspace returns intake prompt."""
    res = dispatch_conversational_turn(workspace=tmp_path)
    assert res["ok"] is True
    assert res["state"] == "intake_needed"
    assert "personalize your personal AI tutor" in res["prompt"]


def test_dispatch_new_topic_triggers_acquisition_gate(tmp_path: Path):
    """Verify requesting a new course topic without dropped books pauses at acquisition gate."""
    init_learner_profile(tmp_path)

    res = dispatch_conversational_turn("Distributed Storage", workspace=tmp_path)
    assert res["ok"] is True
    assert res["state"] == "acquisition_gate"
    assert res["slug"] == "distributed-storage"
    assert "Gold Standard Material Found" in res["prompt"]


def test_dispatch_resolves_acquisition_gate(tmp_path: Path):
    """Verify providing input '1' against acquisition gate resolves checkpoint and advances to blueprint."""
    init_learner_profile(tmp_path)

    # Trigger acquisition gate
    dispatch_conversational_turn("Distributed Storage", workspace=tmp_path)

    # Respond with '1' to proceed with open docs
    res = dispatch_conversational_turn("1", workspace=tmp_path)
    assert res["ok"] is True
    assert res["state"] == "blueprint"
    assert res["action"] == "proceed_open"
    assert "active_artifact" in res
    assert Path(res["active_artifact"]).is_file()


def test_dispatch_active_course_fork_responses(tmp_path: Path):
    """Verify active course routes fork choices 1, 2, 3, and custom questions while preserving the 4-Option Fork."""
    init_learner_profile(tmp_path)
    slug = "study-rust"
    create_course(slug=slug, title="Study Rust", archetype="applied_creation", workspace=tmp_path)

    # 1. Option 1: Next concept
    res_1 = dispatch_conversational_turn("1", workspace=tmp_path, course_slug=slug)
    assert res_1["ok"] is True
    assert res_1["state"] == "teaching"
    assert res_1["action"] == "next_concept"
    assert "Next Action Fork" in res_1["fork_text"]

    # 2. Option 2: Test me
    res_2 = dispatch_conversational_turn("2", workspace=tmp_path, course_slug=slug)
    assert res_2["ok"] is True
    assert res_2["state"] == "testing"
    assert res_2["action"] == "test_inquiry"
    assert "Diagnostic Inquiry" in res_2["diagnostic_prompt"]
    assert "Next Action Fork" in res_2["fork_text"]

    # 3. Option 3: Re-explain / Deeper
    res_3 = dispatch_conversational_turn("3", workspace=tmp_path, course_slug=slug)
    assert res_3["ok"] is True
    assert res_3["state"] == "teaching"
    assert res_3["action"] == "deeper_explanation"
    assert "Next Action Fork" in res_3["fork_text"]

    # 4. Custom inquiry
    res_custom = dispatch_conversational_turn("Can we analyze the memory footprint of this struct?", workspace=tmp_path, course_slug=slug)
    assert res_custom["ok"] is True
    assert res_custom["state"] == "teaching"
    assert res_custom["action"] == "custom_turn"
    assert "Next Action Fork" in res_custom["fork_text"]


def test_tc_cli_dispatch_and_subcommands(tmp_path: Path):
    """Verify tc.py CLI top-level dispatch and preservation of subcommands."""
    tc_script = SCRIPTS_DIR / "tc.py"

    # 1. Top level dispatch on uninitialized workspace
    res_top = subprocess.run(
        [sys.executable, str(tc_script), "dispatch", "--workspace", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
    )
    assert res_top.returncode == 0
    data = json.loads(res_top.stdout)
    assert data["state"] == "intake_needed"

    # 2. Existing subcommands preserved
    for sub in ["init", "extract", "test", "practicals", "notes", "audit", "dag"]:
        res_sub = subprocess.run(
            [sys.executable, str(tc_script), sub, "--help"],
            capture_output=True,
            text=True,
        )
        assert res_sub.returncode == 0
