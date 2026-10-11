"""tests/test_faculty_personas.py — Test suite for Sovereign Faculty personas, packaging manifests, and tag-team handoffs."""

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
SCRIPTS_DIR = REPO_ROOT / "_tc" / "scripts"
TEACH_SCRIPT = SCRIPTS_DIR / "teach_engine.py"
BOOTSTRAP_SCRIPT = SCRIPTS_DIR / "bootstrapper.py"
MEMLOG_SCRIPT = SCRIPTS_DIR / "memlog.py"

EXPECTED_SKILLS = [
    "tc-init",
    "tc-create",
    "tc-teach",
    "tc-test-me",
    "tc-practicals",
    "tc-roadmap",
    "tc-research",
    "tc-verify-course",
    "tc-redirect-course",
    "tc-migrate",
]

EXPECTED_FACULTY = [
    "feynman",
    "euclid",
    "socrates",
    "leonardo",
    "turing",
    "lovelace",
    "newton",
    "marie",
    "aristotle",
    "hypatia",
]


def test_skills_packaging_manifests_and_customization():
    """Verify that all 10 skills possess valid bmod.toml and customize.toml manifests."""
    for skill_name in EXPECTED_SKILLS:
        skill_dir = SKILLS_DIR / skill_name
        assert skill_dir.is_dir(), f"Skill directory missing: {skill_dir}"

        bmod_path = skill_dir / "bmod.toml"
        assert bmod_path.is_file(), f"Missing bmod.toml in {skill_name}"
        bmod_data = tomllib.loads(bmod_path.read_text(encoding="utf-8"))
        assert "skill" in bmod_data
        assert bmod_data["skill"].get("name") == skill_name
        assert bmod_data["skill"].get("version") == "2.0.0"

        cust_path = skill_dir / "customize.toml"
        assert cust_path.is_file(), f"Missing customize.toml in {skill_name}"
        cust_data = tomllib.loads(cust_path.read_text(encoding="utf-8"))
        assert "agent" in cust_data
        assert "persona" in cust_data["agent"]
        assert "title" in cust_data["agent"]
        assert "icon" in cust_data["agent"]


def test_sovereign_faculty_personas_defined():
    """Verify tc-init customize.toml defines all 10 sovereign faculty personas."""
    init_cust = SKILLS_DIR / "tc-init" / "customize.toml"
    assert init_cust.is_file()
    data = tomllib.loads(init_cust.read_text(encoding="utf-8"))

    faculty = data.get("faculty", {}).get("personas", {})
    for expected in EXPECTED_FACULTY:
        assert expected in faculty, f"Faculty persona {expected} missing in tc-init customize.toml"
        p = faculty[expected]
        assert "name" in p
        assert "title" in p
        assert "icon" in p
        assert "style" in p


def test_zero_bmad_references_in_all_skills():
    """Verify zero BMad references across all skill definitions and scripts."""
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        for file_path in skill_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.endswith((".pyc", ".png", ".jpg")):
                try:
                    text = file_path.read_text(encoding="utf-8")
                    assert not re.search(
                        r"\bbmad\b", text, re.IGNORECASE
                    ), f"Found BMad mention in {file_path}"
                except UnicodeDecodeError:
                    pass


def test_teach_fork_tag_team_option():
    """Verify teach_engine fork --tag-team surfaces tag-in option in CLI and JSON."""
    cmd = [sys.executable, str(TEACH_SCRIPT), "fork", "--tag-team", "Euclid", "--json"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert "Tag-in Euclid" in data["text"]
    assert any(opt.get("action") == "tag_team" and opt.get("teacher") == "Euclid" for opt in data["options"])

    # Standard fork without tag-team retains default 4 options
    cmd_default = [sys.executable, str(TEACH_SCRIPT), "fork", "--json"]
    res_def = subprocess.run(cmd_default, capture_output=True, text=True)
    assert res_def.returncode == 0
    data_def = json.loads(res_def.stdout)
    assert len(data_def["options"]) == 4
    assert not any(opt.get("action") == "tag_team" for opt in data_def["options"])


def test_bootstrapper_and_preferences_teacher_persistence(tmp_path: Path):
    """Verify bootstrapper sets, persists, and updates teacher persona."""
    ws = tmp_path / "workspace"
    # Bootstrap with specific teacher
    cmd = [
        sys.executable,
        str(BOOTSTRAP_SCRIPT),
        "bootstrap",
        "--path",
        str(ws),
        "--teacher",
        "socrates",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0

    pref_file = ws / "profile" / "preferences.md"
    assert pref_file.is_file()
    text = pref_file.read_text(encoding="utf-8")
    assert 'teacher: "socrates"' in text
    assert "- **Primary Faculty / Teacher**: socrates" in text

    # Read preferences via CLI
    cmd_pref = [sys.executable, str(BOOTSTRAP_SCRIPT), "preferences", "--path", str(ws)]
    res_pref = subprocess.run(cmd_pref, capture_output=True, text=True)
    assert res_pref.returncode == 0
    data_pref = json.loads(res_pref.stdout)
    assert data_pref["preferences"].get("teacher") == "socrates"

    # Update teacher via set-preferences
    cmd_update = [
        sys.executable,
        str(BOOTSTRAP_SCRIPT),
        "set-preferences",
        "--path",
        str(ws),
        "--teacher",
        "leonardo",
    ]
    res_update = subprocess.run(cmd_update, capture_output=True, text=True)
    assert res_update.returncode == 0

    text_updated = pref_file.read_text(encoding="utf-8")
    assert 'teacher: "leonardo"' in text_updated


def test_teach_engine_session_loads_teacher(tmp_path: Path):
    """Verify teach_engine session reads teacher from profile/preferences.md."""
    ws = tmp_path / "teach_ws"
    ws.mkdir()
    profile_dir = ws / "profile"
    profile_dir.mkdir()
    (profile_dir / "preferences.md").write_text(
        '---\nteacher: "euclid"\nstyle_profile: "direct_technical"\n---\n',
        encoding="utf-8",
    )

    course_dir = ws / "courses" / "sample-course"
    course_dir.mkdir(parents=True)
    (course_dir / "course.toml").write_text(
        """
title = "Sample Course"
slug = "sample-course"

[[chapters]]
id = "ch-01"
title = "Chapter 1"

[[chapters.sections]]
id = "sec-01"
title = "Section 1"
status = "in_progress"
""",
        encoding="utf-8",
    )
    sec_dir = course_dir / "chapter-01" / "section-01"
    sec_dir.mkdir(parents=True)
    (sec_dir / "lesson-plan.md").write_text(
        """---
title: "Lesson Plan"
---
- [ ] 1. Core Axiom
""",
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        str(TEACH_SCRIPT),
        "session",
        "--course",
        "sample-course",
        "--workspace",
        str(ws),
        "--tag-team",
        "Feynman",
        "--json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["preferences"].get("teacher") == "euclid"
    assert "Tag-in Feynman" in data["fork_text"]


def test_memlog_handoff_tag_logging(tmp_path: Path):
    """Verify memlog.py logs atomic tag-team handoffs with structured types."""
    course_dir = tmp_path / "courses" / "sample-course"
    course_dir.mkdir(parents=True)
    memlog_file = course_dir / "memlog.md"

    # Initialize memlog
    cmd_init = [
        sys.executable,
        str(MEMLOG_SCRIPT),
        "init",
        "--path",
        str(memlog_file),
        "--topic",
        "Distributed Systems",
        "--teacher",
        "Feynman",
    ]
    res_init = subprocess.run(cmd_init, capture_output=True, text=True)
    assert res_init.returncode == 0

    # Append handoff
    cmd_handoff = [
        sys.executable,
        str(MEMLOG_SCRIPT),
        "append",
        "--path",
        str(memlog_file),
        "--type",
        "handoff",
        "--by",
        "Feynman",
        "--text",
        "Handing off to Euclid: alternate axiomatic angle on consensus invariants.",
    ]
    res_handoff = subprocess.run(cmd_handoff, capture_output=True, text=True)
    assert res_handoff.returncode == 0

    content = memlog_file.read_text(encoding="utf-8")
    assert "- (handoff by Feynman) Handing off to Euclid: alternate axiomatic angle on consensus invariants." in content

    # Update active teacher
    cmd_set = [
        sys.executable,
        str(MEMLOG_SCRIPT),
        "set",
        "--path",
        str(memlog_file),
        "--key",
        "teacher",
        "--value",
        "Euclid",
    ]
    res_set = subprocess.run(cmd_set, capture_output=True, text=True)
    assert res_set.returncode == 0

    content_updated = memlog_file.read_text(encoding="utf-8")
    assert "teacher: Euclid" in content_updated
