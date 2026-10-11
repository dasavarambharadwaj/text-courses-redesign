"""test_beginner_adaptation.py — Verification for FR-34 Beginner-to-Core Pedagogical Adaptation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCOUT_SCRIPT = Path("_tc/scripts/scout.py").resolve()
COURSE_BUILDER_SCRIPT = Path("_tc/scripts/course_builder.py").resolve()
TEACH_ENGINE_SCRIPT = Path("_tc/scripts/teach_engine.py").resolve()
DIAGNOSTIC_TESTER_SCRIPT = Path("_tc/scripts/diagnostic_tester.py").resolve()


def test_scout_beginner_hat_prioritization(tmp_path: Path):
    """Verify that scout --beginner prioritizes beginner friction hunter and intuitive metaphorist."""
    res = subprocess.run(
        [
            sys.executable,
            str(SCOUT_SCRIPT),
            "scout",
            "--slug",
            "distributed-basics",
            "--workspace",
            str(tmp_path),
            "--topic",
            "Distributed Consensus and State Machines",
            "--beginner",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True

    critique_file = Path(data["critique_file"])
    assert critique_file.is_file()
    critique_text = critique_file.read_text(encoding="utf-8")

    # In beginner mode, Hat 1 is Beginner Friction Hunter and Hat 2 is Intuitive Metaphorist
    assert "Hat 1: Beginner Friction Hunter" in critique_text
    assert "Hat 2: Intuitive Metaphorist" in critique_text


def test_course_builder_beginner_scaffolding(tmp_path: Path):
    """Verify course builder detects beginner profile and scaffolds foundational stepping stone chapter."""
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir(parents=True)
    pref_file = profile_dir / "preferences.md"
    pref_file.write_text(
        "# Learner Preferences\n"
        "competency_level: beginner\n"
        "role: Novice Programmer\n"
        "style_profile: direct_technical\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            str(COURSE_BUILDER_SCRIPT),
            "create",
            "--slug",
            "intro-python",
            "--workspace",
            str(tmp_path),
            "--title",
            "Python Foundations",
            "--topic",
            "Python control flow, functions, and data structures",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True

    course_toml = tmp_path / "courses" / "intro-python" / "course.toml"
    assert course_toml.is_file()
    content = course_toml.read_text(encoding="utf-8")
    assert 'competency_level = "beginner"' in content

    # Chapter 01 must be Foundations & Intuitive Primitives
    overview_file = tmp_path / "courses" / "intro-python" / "overview.md"
    assert overview_file.is_file()
    overview_text = overview_file.read_text(encoding="utf-8")
    assert "Foundations, Mental Models & Intuitive Primitives" in overview_text


def test_teach_engine_and_tester_beginner_guidance(tmp_path: Path):
    """Verify teach engine and diagnostic tester supply empathetic beginner guidance."""
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "preferences.md").write_text(
        "competency_level: beginner\nrole: Beginner Learner\n",
        encoding="utf-8",
    )

    # Create beginner course
    subprocess.run(
        [
            sys.executable,
            str(COURSE_BUILDER_SCRIPT),
            "create",
            "--slug",
            "beginner-rust",
            "--workspace",
            str(tmp_path),
            "--title",
            "Rust For Beginners",
            "--topic",
            "Ownership and borrowing",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # 1. Teach engine session
    res_teach = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE_SCRIPT),
            "session",
            "--course",
            "beginner-rust",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_teach.returncode == 0
    t_data = json.loads(res_teach.stdout)
    assert t_data["is_beginner"] is True
    assert "Hypatia" in t_data["pedagogical_guidance"]
    assert "zero unexplained jargon" in t_data["pedagogical_guidance"].lower()

    # 2. Diagnostic tester active context
    res_test = subprocess.run(
        [
            sys.executable,
            str(DIAGNOSTIC_TESTER_SCRIPT),
            "prepare",
            "--course",
            str(tmp_path / "courses" / "beginner-rust"),
        ],
        capture_output=True,
        text=True,
    )
    # May be exit 1 if no section is yet in review, but check with completed section
    # Let's advance section to review first
    res_adv = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE_SCRIPT),
            "advance",
            "--course",
            "beginner-rust",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_adv.returncode == 0

    # Advance second concept to reach review
    subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE_SCRIPT),
            "advance",
            "--course",
            "beginner-rust",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    res_test_ready = subprocess.run(
        [
            sys.executable,
            str(DIAGNOSTIC_TESTER_SCRIPT),
            "prepare",
            "--course",
            str(tmp_path / "courses" / "beginner-rust"),
        ],
        capture_output=True,
        text=True,
    )
    assert res_test_ready.returncode == 0
    test_data = json.loads(res_test_ready.stdout)
    assert test_data["is_beginner"] is True
    assert "Beginner Focus Active" in test_data["beginner_guidance"]
