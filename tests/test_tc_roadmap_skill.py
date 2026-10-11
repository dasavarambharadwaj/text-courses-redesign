"""tests/test_tc_roadmap_skill.py — Unit tests for tc-roadmap skill (FR-26, FR-27).

Validates:
- SKILL.md file existence and valid YAML frontmatter
- Persona definition: Aristotle (The Cartographer)
- Triad Inception Roundtable Party Mode caucus: Marie, Aristotle, Hypatia
- Diagnostic placement testing and course waiving protocol
- Manifest & DAG commands referencing _tc/scripts/
- Strict zero-BMad references
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_FILE = Path(__file__).parent.parent / "skills" / "tc-roadmap" / "SKILL.md"


def test_tc_roadmap_skill_exists_and_frontmatter():
    """Verify tc-roadmap SKILL.md exists and has valid metadata."""
    assert SKILL_FILE.is_file(), f"Missing {SKILL_FILE}"
    content = SKILL_FILE.read_text(encoding="utf-8")

    assert content.startswith("---")
    assert "name: tc-roadmap" in content
    assert "description:" in content


def test_tc_roadmap_triad_personas():
    """Verify Aristotle persona and Triad Inception caucus members are defined."""
    content = SKILL_FILE.read_text(encoding="utf-8")

    assert "Aristotle" in content
    assert "Cartographer" in content
    assert "Marie" in content
    assert "Hypatia" in content
    assert "Party Mode" in content or "Roundtable" in content


def test_tc_roadmap_mechanics_and_scripts():
    """Verify diagnostic placement and runtime script commands are present."""
    content = SKILL_FILE.read_text(encoding="utf-8")

    assert "placement" in content.lower()
    assert "waived" in content.lower() or "waive" in content.lower()
    assert "_tc/scripts/manifest.py" in content
    assert "_tc/scripts/dag.py" in content
    assert "roadmap.toml" in content
    assert "tc-create" in content


def test_tc_roadmap_zero_bmad_references():
    """Verify strict zero-BMad mentions in tc-roadmap skill documentation."""
    content = SKILL_FILE.read_text(encoding="utf-8")
    assert not re.search(r"\bbmad\b", content, re.IGNORECASE), "Found forbidden BMad reference in tc-roadmap"
