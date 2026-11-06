"""tests/test_dispatcher_continuation.py — Tests for tc.py dispatcher lifecycle continuation and gate transitions (CAP-1, FR-46)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from tc import dispatch_conversational_turn


def setup_test_profile(ws: Path) -> None:
    """Helper to initialize canonical _tc/ profile preferences."""
    pref_dir = ws / "_tc" / "profile"
    pref_dir.mkdir(parents=True, exist_ok=True)
    pref_file = pref_dir / "preferences.md"
    pref_file.write_text(
        "---\nname: Test Learner\nexperience: intermediate\npracticals: true\nmode: interactive\n---\n",
        encoding="utf-8",
    )


def test_dispatch_intake_needed_on_fresh_workspace(tmp_path: Path) -> None:
    """Verify dispatch on uninitialized workspace reports intake_needed."""
    res = dispatch_conversational_turn(workspace=tmp_path)
    assert res["ok"] is True
    assert res["state"] == "intake_needed"
    assert "prompt" in res
    assert "Welcome to **TextCourses**" in res["prompt"]


def test_dispatch_acquisition_gate_pause(tmp_path: Path) -> None:
    """Verify dispatch on new topic pauses at acquisition gate when no local docs exist."""
    setup_test_profile(tmp_path)
    res = dispatch_conversational_turn("Distributed Storage", workspace=tmp_path)
    assert res["ok"] is True
    assert res["state"] == "acquisition_gate"
    assert res["slug"] == "distributed-storage"
    assert "Gold Standard Material Found" in res["prompt"]
    assert len(res.get("options", [])) >= 2


def test_dispatch_proceed_open_advances_to_blueprint_state(tmp_path: Path) -> None:
    """Verify '1' (proceed_open) does not dead-end at creating_course, but advances to blueprint."""
    setup_test_profile(tmp_path)

    # 1. Trigger acquisition gate
    dispatch_conversational_turn("Distributed Storage", workspace=tmp_path)

    # 2. Respond with '1' to proceed with open documentation
    res = dispatch_conversational_turn("1", workspace=tmp_path)
    assert res["ok"] is True
    # Invariant: must not dead-end at creating_course
    assert res["state"] == "blueprint", f"Expected 'blueprint', got '{res['state']}'"
    assert res["action"] == "proceed_open"
    assert res["slug"] == "distributed-storage"

    # Invariant: must return active artifact pointing to blueprint
    assert "active_artifact" in res
    blueprint_path = Path(res["active_artifact"])
    assert blueprint_path.is_file(), f"Blueprint file not found at {blueprint_path}"
    assert "Course Blueprint" in blueprint_path.read_text(encoding="utf-8")

    # Invariant: approval gate options must be active
    assert "prompt" in res
    assert any(opt["action"] == "start_lesson" for opt in res.get("options", []))


def test_dispatch_approval_gate_proceeds_to_teaching(tmp_path: Path) -> None:
    """Verify responding '1' at Curriculum Approval Gate launches first lesson in teaching state."""
    setup_test_profile(tmp_path)

    # 1. Trigger acquisition gate
    dispatch_conversational_turn("Distributed Storage", workspace=tmp_path)

    # 2. Advance through acquisition gate to blueprint
    res_bp = dispatch_conversational_turn("1", workspace=tmp_path)
    assert res_bp["state"] == "blueprint"

    # 3. Approve blueprint with '1' to start lesson
    res_teach = dispatch_conversational_turn("1", workspace=tmp_path)
    assert res_teach["ok"] is True
    assert res_teach["state"] == "teaching"
    assert res_teach["action"] == "start_lesson"
    assert "context" in res_teach
    assert "fork_text" in res_teach
    assert "Next Action Fork" in res_teach["fork_text"]


def test_dispatch_teaching_fork_turns(tmp_path: Path) -> None:
    """Verify instructional turns route through the 4-Option Action Fork cleanly."""
    setup_test_profile(tmp_path)

    # Fast-forward to teaching state
    dispatch_conversational_turn("Distributed Storage", workspace=tmp_path)
    dispatch_conversational_turn("1", workspace=tmp_path)  # To blueprint
    dispatch_conversational_turn("1", workspace=tmp_path)  # To teaching

    slug = "distributed-storage"

    # [1] Next Concept
    res_1 = dispatch_conversational_turn("1", workspace=tmp_path, course_slug=slug)
    assert res_1["ok"] is True
    assert res_1["state"] == "teaching"
    assert res_1["action"] == "next_concept"

    # [2] Test Me
    res_2 = dispatch_conversational_turn("2", workspace=tmp_path, course_slug=slug)
    assert res_2["ok"] is True
    assert res_2["state"] == "testing"
    assert res_2["action"] == "test_inquiry"

    # [3] Deeper / Re-explain
    res_3 = dispatch_conversational_turn("3", workspace=tmp_path, course_slug=slug)
    assert res_3["ok"] is True
    assert res_3["state"] == "teaching"
    assert res_3["action"] == "deeper_explanation"

    # [4] Custom question
    res_4 = dispatch_conversational_turn("Can we check the crash-recovery model?", workspace=tmp_path, course_slug=slug)
    assert res_4["ok"] is True
    assert res_4["state"] == "teaching"
    assert res_4["action"] == "custom_turn"
