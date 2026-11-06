"""tests/test_public_surface.py — Invariant tests for single public /tc surface and internal encapsulation (FR-46, CAP-1)."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_skills_directory_contains_solely_tc() -> None:
    """FR-46: skills/ must contain solely tc/ and zero other tc-* packages."""
    skills_dir = REPO_ROOT / "skills"
    assert skills_dir.is_dir(), "skills/ directory must exist"

    child_dirs = [d.name for d in skills_dir.iterdir() if d.is_dir()]
    assert child_dirs == ["tc"], f"Expected solely ['tc'] under skills/, but found: {child_dirs}"


def test_skills_lock_exports_solely_tc() -> None:
    """FR-46: skills-lock.json must export tc and zero other tc-* packages."""
    lock_file = REPO_ROOT / "skills-lock.json"
    assert lock_file.is_file(), "skills-lock.json must exist"

    data = json.loads(lock_file.read_text(encoding="utf-8"))
    skills = data.get("skills", {})

    assert "tc" in skills, "skills-lock.json must export 'tc'"
    tc_entry = skills["tc"]
    assert tc_entry.get("skillPath") == "skills/tc/SKILL.md"

    # Enforce zero tc-* packages exported
    tc_prefixed = [k for k in skills if k.startswith("tc-")]
    assert tc_prefixed == [], f"Found forbidden internal packages in skills-lock.json: {tc_prefixed}"


def test_internal_capability_packages_encapsulated() -> None:
    """FR-46: All internal capability packages must reside under _tc/skills/."""
    internal_skills_dir = REPO_ROOT / "_tc" / "skills"
    assert internal_skills_dir.is_dir(), "_tc/skills/ directory must exist"

    expected_internal = {
        "tc-create",
        "tc-index",
        "tc-init",
        "tc-migrate",
        "tc-practicals",
        "tc-redirect-course",
        "tc-research",
        "tc-roadmap",
        "tc-teach",
        "tc-test-me",
        "tc-verify-course",
    }

    found_dirs = {d.name for d in internal_skills_dir.iterdir() if d.is_dir()}
    for exp in expected_internal:
        assert exp in found_dirs, f"Expected internal skill '{exp}' under _tc/skills/"
        skill_md = internal_skills_dir / exp / "SKILL.md"
        assert skill_md.is_file(), f"Expected SKILL.md in _tc/skills/{exp}"


def test_public_skill_md_contract() -> None:
    """CAP-1 / FR-46: skills/tc/SKILL.md must route through dispatcher and omit obsolete subcommands."""
    tc_skill_md = REPO_ROOT / "skills" / "tc" / "SKILL.md"
    assert tc_skill_md.is_file(), "skills/tc/SKILL.md must exist"

    content = tc_skill_md.read_text(encoding="utf-8")

    # Must invoke dispatcher
    assert "tc.py dispatch" in content, "skills/tc/SKILL.md must instruct invoking tc.py dispatch"

    # Must not contain uv run
    assert "uv run" not in content, "skills/tc/SKILL.md must not reference uv run"

    # Must not expose subcommands as public commands
    assert "Power-User Subcommands" not in content, "skills/tc/SKILL.md must not expose power-user subcommands"
