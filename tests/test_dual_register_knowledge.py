"""tests/test_dual_register_knowledge.py — Test suite for Dual-Register Knowledge Synthesis (FR-32).

Validates:
- Human-First notes in plain accessible English with intuitive analogies and teacher attribution
- Flat chapter textbook updates in courses/<slug>/notes/chapter-XX.md
- AI-First token-minimal memlog notation in courses/<slug>/memlog.md
- Closed conversation tracing: teach_engine concept advancement & question logging
- Closed conversation tracing: diagnostic_tester misconception & milestone mirroring
- Strict Zero-BMad references in scripts and skills
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

NOTES_COMPILER = Path(__file__).parent.parent / "_tc" / "scripts" / "notes_compiler.py"
TEACH_ENGINE = Path(__file__).parent.parent / "_tc" / "scripts" / "teach_engine.py"
DIAG_TESTER = Path(__file__).parent.parent / "_tc" / "scripts" / "diagnostic_tester.py"
MEMLOG_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "memlog.py"
TEACH_SKILL = Path(__file__).parent.parent / "skills" / "tc-teach" / "SKILL.md"
TEST_SKILL = Path(__file__).parent.parent / "skills" / "tc-test-me" / "SKILL.md"


def test_zero_bmad_references():
    """Verify strict zero-BMad references across all dual-register scripts and skills."""
    targets = [NOTES_COMPILER, TEACH_ENGINE, DIAG_TESTER, MEMLOG_SCRIPT, TEACH_SKILL, TEST_SKILL]
    for target in targets:
        text = target.read_text(encoding="utf-8")
        assert not re.search(r"\bbmad\b", text, re.IGNORECASE), f"Found BMad mention in {target}"


def test_human_first_notes_compilation(tmp_path: Path):
    """Verify notes_compiler produces human-first English notes with analogy and teacher attribution."""
    course_dir = tmp_path / "courses" / "concurrency-101"
    sec_dir = course_dir / "chapter-01" / "section-01"
    sec_dir.mkdir(parents=True, exist_ok=True)

    # Scaffolding course.toml and memlog.md
    (course_dir / "course.toml").write_text(
        'course = { id = "concurrency-101", title = "Concurrency 101" }\n'
        'chapters = [\n'
        '  { id = "chapter-01", title = "Pointers & Memory", sections = [\n'
        '    { id = "sec-01", title = "Atomic Compare-And-Swap", status = "in_progress" }\n'
        '  ]}\n'
        ']\n',
        encoding="utf-8",
    )
    (course_dir / "memlog.md").write_text(
        "---\ncourse: concurrency-101\n---\n# Course Pedagogical Memory\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            str(NOTES_COMPILER),
            "compile",
            "--section-dir",
            str(sec_dir),
            "--title",
            "Atomic Compare-And-Swap",
            "--recap",
            "CAS provides atomic lock-free mutation.",
            "Hardware compares memory address against expected value before updating.",
            "Eliminates mutex locks in high-throughput data structures.",
            "--analogy",
            "Think of CAS like trading tokens: you show the cashier your old token, and only if it matches does she swap it for the new token in one fluid motion.",
            "--teacher",
            "⚡ Richard Feynman",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Error: {res.stderr}"
    data = json.loads(res.stdout)
    assert data["ok"] is True

    # 1. Check section notes.md
    notes_file = sec_dir / "notes.md"
    assert notes_file.is_file()
    notes_text = notes_file.read_text(encoding="utf-8")
    assert "*Distilled by ⚡ Richard Feynman*" in notes_text
    assert "## 3-Bullet Recap (In Plain English)" in notes_text
    assert "## Intuitive Mental Model & Analogy" in notes_text
    assert "trading tokens" in notes_text
    assert "## Core Mechanics & Architecture" in notes_text

    # 2. Check flat chapter textbook notes
    ch_notes_file = course_dir / "notes" / "chapter-01.md"
    assert ch_notes_file.is_file()
    ch_text = ch_notes_file.read_text(encoding="utf-8")
    assert "Atomic Compare-And-Swap" in ch_text

    # 3. Check token-minimal memlog milestone
    memlog_text = (course_dir / "memlog.md").read_text(encoding="utf-8")
    assert "- (milestone) sec:section-01:status=review:notes_compiled" in memlog_text


def test_closed_tracing_loop_teach_and_test(tmp_path: Path):
    """Verify teach_engine and diagnostic_tester trace concepts, questions, and misconceptions into memlog."""
    course_dir = tmp_path / "courses" / "kv-store"
    sec_dir = course_dir / "chapter-01" / "section-01"
    sec_dir.mkdir(parents=True, exist_ok=True)

    # Scaffolding profile/preferences.md
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "preferences.md").write_text(
        "---\nrole: Systems Engineer\nteacher: feynman\n---\n",
        encoding="utf-8",
    )

    # Scaffolding course.toml and lesson-plan.md
    (course_dir / "course.toml").write_text(
        'course = { id = "kv-store", title = "Key-Value Store", status = "in_progress" }\n'
        'chapters = [\n'
        '  { id = "chapter-01", title = "Storage Engine", sections = [\n'
        '    { id = "sec-01", title = "LSM MemTable", status = "in_progress" }\n'
        '  ]}\n'
        ']\n',
        encoding="utf-8",
    )
    (course_dir / "memlog.md").write_text(
        "---\ncourse: kv-store\n---\n# Course Pedagogical Memory\n",
        encoding="utf-8",
    )
    (sec_dir / "lesson-plan.md").write_text(
        "# Lesson Plan: LSM MemTable\n"
        "## Objectives\n"
        "- [ ] Understand in-memory SkipList ordering\n"
        "- [ ] Implement WAL durability append\n",
        encoding="utf-8",
    )

    # 1. Tick concept via teach_engine
    res_adv1 = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE),
            "advance",
            "--course",
            "kv-store",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_adv1.returncode == 0
    memlog_text1 = (course_dir / "memlog.md").read_text(encoding="utf-8")
    assert "- (concept by Feynman) sec-01:understand_in_memory_skiplist_ordering:mastered" in memlog_text1

    # 2. Log learner question via teach_engine
    res_q = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE),
            "log-question",
            "--course",
            "kv-store",
            "--workspace",
            str(tmp_path),
            "--text",
            "Why use a SkipList over a Red-Black Tree?",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_q.returncode == 0
    memlog_text2 = (course_dir / "memlog.md").read_text(encoding="utf-8")
    assert "- (question) q:Why use a SkipList over a Red-Black Tree?" in memlog_text2

    # 3. Advance second concept to complete section
    res_adv2 = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE),
            "advance",
            "--course",
            "kv-store",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_adv2.returncode == 0
    memlog_text3 = (course_dir / "memlog.md").read_text(encoding="utf-8")
    assert "- (milestone) sec:sec-01:all_concepts_mastered" in memlog_text3

    # Section is now in 'review' status, ready for diagnostic testing
    # 4. Diagnostic test failure: records misconception to test-ledger and memlog
    res_fail = subprocess.run(
        [
            sys.executable,
            str(DIAG_TESTER),
            "record",
            "--course",
            str(course_dir),
            "--chapter",
            "chapter-01",
            "--section",
            "sec-01",
            "--type",
            "hinge_scenario",
            "--prompt",
            "What happens if power is cut before WAL flush?",
            "--response",
            "MemTable still has it in RAM so it is saved",
            "--outcome",
            "fail",
            "--misconception",
            "CONFUSION_VOLATILE_MEMORY_PERSISTENCE",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_fail.returncode == 0
    memlog_text4 = (course_dir / "memlog.md").read_text(encoding="utf-8")
    assert "- (misconception) misc:confusion_volatile_memory_persistence:sec-01" in memlog_text4

    # 5. Diagnostic test pass: records milestone to test-ledger and memlog, completing section
    res_pass = subprocess.run(
        [
            sys.executable,
            str(DIAG_TESTER),
            "record",
            "--course",
            str(course_dir),
            "--chapter",
            "chapter-01",
            "--section",
            "sec-01",
            "--type",
            "hinge_scenario",
            "--prompt",
            "What happens if power is cut before WAL flush?",
            "--response",
            "Data is lost because RAM is volatile without fsync",
            "--outcome",
            "pass",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_pass.returncode == 0
    memlog_text5 = (course_dir / "memlog.md").read_text(encoding="utf-8")
    assert "- (milestone) test:passed:sec-01:completed" in memlog_text5
    assert "- (milestone) course:completed:kv-store" in memlog_text5
