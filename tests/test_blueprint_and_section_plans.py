"""tests/test_blueprint_and_section_plans.py — Tests for Course Blueprint Approval Gate & High-Density Section Plans (CAP-2, AD-4)."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from course_builder import create_course, scaffold_course_files
from checkpoint_manager import GATE_APPROVAL, create_approval_gate, handle_gate_response, load_checkpoint
from source_mapper import compile_source_map, read_source_pointer


def test_blueprint_and_high_density_section_plans_scaffolded(tmp_path: Path):
    """Verify scaffolding generates _tc/courses/<slug>/blueprint.md and high-density section plans."""
    slug = "compiler-internals"
    course_data = {
        "course": {
            "id": slug,
            "title": "Compiler Internals & Optimization",
            "archetype": "applied_creation",
        },
        "chapters": [
            {
                "id": "chapter-01",
                "title": "Lexical Analysis & Parsing",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "Deterministic Finite Automata",
                        "vocabulary_introduced": ["DFA", "State Transition"],
                        "prerequisites": [],
                    },
                    {
                        "id": "sec-02",
                        "title": "Recursive Descent LL(k)",
                        "vocabulary_introduced": ["AST", "Backtracking"],
                        "prerequisites": ["DFA"],
                    },
                ],
            },
        ],
    }

    # Create mock converted markdown source in _tc/research/<slug>/sources/markdown/
    src_dir = tmp_path / "_tc" / "research" / slug / "sources" / "markdown"
    src_dir.mkdir(parents=True, exist_ok=True)
    dragon_book = src_dir / "dragon_book.md"
    dragon_book.write_text(
        "# Compilers: Principles and Techniques\n\n"
        "## Deterministic Finite Automata\n"
        "A DFA consists of a finite set of states S and transitions.\n"
        "State Transition semantics are deterministic.\n\n"
        "## Recursive Descent LL(k)\n"
        "An AST node represents a grammar production rule with no backtracking.\n",
        encoding="utf-8",
    )

    scaffold_course_files(
        tmp_path,
        course_data,
        deliberation_md="Triad verified parser theory and compiler pipeline coverage.",
    )

    # 1. Verify blueprint.md
    bp_tc = tmp_path / "_tc" / "courses" / slug / "blueprint.md"
    bp_course = tmp_path / "courses" / slug / ".tc" / "blueprint.md"
    assert bp_tc.is_file(), "_tc/courses/<slug>/blueprint.md must exist"
    assert bp_course.is_file(), "courses/<slug>/.tc/blueprint.md must exist"

    bp_content = bp_tc.read_text(encoding="utf-8")
    assert "Course Blueprint: Compiler Internals & Optimization" in bp_content
    assert "Applied Creation" in bp_content
    assert "Lexical Analysis & Parsing" in bp_content
    assert "Deterministic Finite Automata" in bp_content
    assert "Bloom Diagnostic Probes" in bp_content
    assert "Failure Injection Protocols" in bp_content

    # 2. Verify source-map.toml generated in _tc/courses/<slug>/
    sm_path = tmp_path / "_tc" / "courses" / slug / "source-map.toml"
    assert sm_path.is_file(), "Canonical _tc/courses/<slug>/source-map.toml must exist"

    # 3. Verify section plans in both _tc/ and courses/<slug>/.tc/
    tc_plan = tmp_path / "_tc" / "courses" / slug / "plans" / "chapter-01-lexical-analysis-parsing" / "section-01-deterministic-finite-automata" / "lesson-plan.md"
    legacy_plan = tmp_path / "courses" / slug / ".tc" / "plans" / "chapter-01-lexical-analysis-parsing" / "section-01-deterministic-finite-automata" / "lesson-plan.md"
    assert tc_plan.is_file(), "Canonical section plan must exist"
    assert legacy_plan.is_file(), "Legacy section plan must exist"

    plan_text = tc_plan.read_text(encoding="utf-8")
    # Verify Teaching Plan
    assert "## Teaching Plan" in plan_text
    assert "Intuitive Metaphor & Core Invariant" in plan_text
    assert "Technical Formalism" in plan_text
    assert "Applied Practical Exercise" in plan_text

    # Verify Source-Coverage Map
    assert "## Source-Coverage Map" in plan_text
    assert "dragon_book" in plan_text or "_tc/research" in plan_text
    assert "Lines" in plan_text

    # Verify Verification Plan
    assert "## Verification Plan" in plan_text
    assert "Bloom Diagnostic Probes" in plan_text
    assert "Bloom Level 2 (Comprehension)" in plan_text
    assert "Bloom Level 4 (Analysis)" in plan_text
    assert "Bloom Level 5 (Evaluation)" in plan_text
    assert "Failure Injection Scenario" in plan_text
    assert "Explicit Mastery Criteria" in plan_text


def test_gate_2_curriculum_approval_gate(tmp_path: Path):
    """Verify Gate 2 displays blueprint roadmap and responds to start vs adjust."""
    slug = "db-internals"
    course_data = {
        "chapters": [
            {
                "title": "Storage Engine Core",
                "sections": [{"title": "Page Cache"}, {"title": "WAL"}],
            }
        ]
    }
    # Create dummy blueprint
    bp = tmp_path / "_tc" / "courses" / slug / "blueprint.md"
    bp.parent.mkdir(parents=True, exist_ok=True)
    bp.write_text("# Blueprint\n", encoding="utf-8")

    gate = create_approval_gate(
        workspace=tmp_path,
        slug=slug,
        title="Database Internals",
        course_data=course_data,
        deliberation_summary="100% textbook coverage verified.",
    )
    assert gate["gate"] == GATE_APPROVAL
    assert "Database Internals" in gate["prompt"]
    assert "Storage Engine Core" in gate["prompt"]
    assert "Page Cache" in gate["prompt"]
    assert "_tc/courses/db-internals/blueprint.md" in gate["prompt"]
    assert gate["blueprint_path"] == str(bp)

    # User selects Start Lesson 1
    res = handle_gate_response("1", workspace=tmp_path)
    assert res["ok"] is True
    assert res["has_active_gate"] is False
    assert res["action"] == "start_lesson"
    assert load_checkpoint(tmp_path) is None
