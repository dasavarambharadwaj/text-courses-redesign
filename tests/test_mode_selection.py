"""tests/test_mode_selection.py — Unit and integration tests for execution mode selection and unattended auto creation (CAP-7, FR-47)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from bootstrapper import bootstrap_workspace, parse_preferences_file, compile_preferences_content, atomic_write_text
from tc import dispatch_conversational_turn


def test_preferences_mode_persistence(tmp_path: Path) -> None:
    """FR-47: Verify mode is persisted to _tc/profile/preferences.md and parsed correctly."""
    ws = tmp_path / "ws_mode_test"
    bootstrap_workspace(ws, mode="auto")

    pref_file = ws / "_tc" / "profile" / "preferences.md"
    assert pref_file.is_file(), "Preferences file must exist"
    content = pref_file.read_text(encoding="utf-8")
    assert 'mode: "auto"' in content

    parsed = parse_preferences_file(pref_file)
    assert parsed.get("mode") == "auto"

    # Update mode to interactive
    updated_content = compile_preferences_content(
        role=parsed.get("role", "Software Engineer"),
        domain_experience=parsed.get("domain_experience", "intermediate"),
        explanation_density=parsed.get("explanation_density", "balanced"),
        teacher=parsed.get("teacher", "feynman"),
        mode="interactive",
    )
    atomic_write_text(pref_file, updated_content)

    re_parsed = parse_preferences_file(pref_file)
    assert re_parsed.get("mode") == "interactive"


def test_interactive_mode_pauses_at_creation_checkpoints(tmp_path: Path) -> None:
    """CAP-7 / FR-47: Interactive mode must pause at Acquisition Gate and Curriculum Approval Gate."""
    ws = tmp_path / "ws_interactive"
    bootstrap_workspace(ws, mode="interactive")

    # Turn 1: Dispatch topic -> pauses at acquisition gate
    res_1 = dispatch_conversational_turn("Distributed Storage", workspace=ws)
    assert res_1["ok"] is True
    assert res_1["state"] == "acquisition_gate"
    assert "options" in res_1

    # Turn 2: Learner approves open docs -> advances to blueprint gate and pauses
    res_2 = dispatch_conversational_turn("1", workspace=ws)
    assert res_2["ok"] is True
    assert res_2["state"] == "blueprint"
    assert "active_artifact" in res_2
    assert Path(res_2["active_artifact"]).is_file()

    # Turn 3: Learner approves blueprint -> advances to teaching
    res_3 = dispatch_conversational_turn("1", workspace=ws)
    assert res_3["ok"] is True
    assert res_3["state"] == "teaching"
    assert res_3["action"] == "start_lesson"


def test_auto_mode_unattended_creation_pipeline(tmp_path: Path) -> None:
    """CAP-7 / FR-47: Auto mode executes entire creation unattended, logs decisions, and lands in teaching."""
    ws = tmp_path / "ws_auto"
    bootstrap_workspace(ws, mode="auto")

    # Dispatch topic in auto mode -> executes research, course building, blueprint approval without pausing
    res = dispatch_conversational_turn("Async Rust Runtime", workspace=ws)
    assert res["ok"] is True
    assert res["state"] == "teaching"
    assert res["action"] == "auto_created"
    assert res["mode"] == "auto"
    assert res["slug"] == "async-rust-runtime"
    assert "context" in res
    assert "fork_text" in res

    # Verify decisions logged in memlogs
    prof_memlog = ws / "_tc" / "profile" / "memlog.md"
    assert prof_memlog.is_file()
    prof_text = prof_memlog.read_text(encoding="utf-8")
    assert "Auto-mode" in prof_text or "decision" in prof_text

    course_memlog = ws / "_tc" / "courses" / "async-rust-runtime" / "memlog.md"
    if not course_memlog.is_file():
        course_memlog = ws / "courses" / "async-rust-runtime" / ".tc" / "memlog.md"
    assert course_memlog.is_file()
    course_text = course_memlog.read_text(encoding="utf-8")
    assert "Auto-mode" in course_text or "decision" in course_text


def test_teaching_parity_across_both_modes(tmp_path: Path) -> None:
    """FR-47: Teaching behavior is 100% identical in both interactive and auto modes."""
    # Setup interactive workspace
    ws_int = tmp_path / "ws_parity_int"
    bootstrap_workspace(ws_int, mode="interactive")
    dispatch_conversational_turn("Event Loop Architecture", workspace=ws_int)
    dispatch_conversational_turn("1", workspace=ws_int)  # To blueprint
    dispatch_conversational_turn("1", workspace=ws_int)  # To teaching

    # Setup auto workspace
    ws_auto = tmp_path / "ws_parity_auto"
    bootstrap_workspace(ws_auto, mode="auto")
    dispatch_conversational_turn("Event Loop Architecture", workspace=ws_auto)  # Direct to teaching

    slug = "event-loop-architecture"

    # In both modes, [1] advances concept
    res_int_1 = dispatch_conversational_turn("1", workspace=ws_int, course_slug=slug)
    res_auto_1 = dispatch_conversational_turn("1", workspace=ws_auto, course_slug=slug)
    assert res_int_1["state"] == res_auto_1["state"] == "teaching"
    assert res_int_1["action"] == res_auto_1["action"] == "next_concept"

    # In both modes, [2] triggers test inquiry
    res_int_2 = dispatch_conversational_turn("2", workspace=ws_int, course_slug=slug)
    res_auto_2 = dispatch_conversational_turn("2", workspace=ws_auto, course_slug=slug)
    assert res_int_2["state"] == res_auto_2["state"] == "testing"
    assert res_int_2["action"] == res_auto_2["action"] == "test_inquiry"

    # In both modes, [3] triggers deeper explanation
    res_int_3 = dispatch_conversational_turn("3", workspace=ws_int, course_slug=slug)
    res_auto_3 = dispatch_conversational_turn("3", workspace=ws_auto, course_slug=slug)
    assert res_int_3["state"] == res_auto_3["state"] == "teaching"
    assert res_int_3["action"] == res_auto_3["action"] == "deeper_explanation"
