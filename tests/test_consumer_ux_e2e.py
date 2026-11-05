"""tests/test_consumer_ux_e2e.py — End-to-End Consumer UX Integration Suite & Zero-BMad Audit."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
TESTS_DIR = Path(__file__).resolve().parent

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from extractor import auto_ingest_workspace
from course_builder import create_course
from checkpoint_manager import create_approval_gate, handle_gate_response, load_checkpoint
from teach_engine import get_teaching_session, advance_lesson_concept


def create_searchable_textbook(path: Path) -> Path:
    """Create a multi-section searchable PDF textbook."""
    raw_pdf = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 200 >>
stream
BT
/F1 12 Tf
72 712 Td
(Chapter 1: Distributed Transactions and Consensus Mechanics) Tj
0 -24 Td
(In two-phase commit, the coordinator sends prepare requests to all participants.) Tj
0 -24 Td
(Atomic broadcast guarantees identical delivery order across all non-faulty nodes.) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000495 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
575
%%EOF"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw_pdf)
    return path


def test_consumer_ux_complete_lifecycle(tmp_path: Path):
    """Verify complete drop-in to lesson workflow with checkpoints, clean workspace, and bounded summary."""
    # Step 1: Initialize learner preferences
    pref_file = tmp_path / "profile" / "preferences.md"
    pref_file.parent.mkdir(parents=True, exist_ok=True)
    pref_file.write_text(
        "role: Infrastructure Engineer\ncompetency_level: intermediate\npractical_focus: true\n",
        encoding="utf-8",
    )

    # Step 2: Drop textbook PDF into workspace books/ directory
    book_path = create_searchable_textbook(tmp_path / "books" / "distributed-consensus.pdf")
    assert book_path.is_file()

    # Step 3: Auto-ingest runs silently
    ingest_res = auto_ingest_workspace(tmp_path)
    assert ingest_res["ok"] is True
    assert ingest_res["total_extracted"] == 1
    assert ingest_res["has_scanned_warnings"] is False

    # Step 4: Curriculum synthesis with <= 40-word deliberation summary
    slug = "dist-consensus"
    course_res = create_course(
        slug=slug,
        title="Distributed Consensus Engineering",
        archetype="applied_creation",
        workspace=tmp_path,
    )
    assert course_res["ok"] is True
    summary = course_res.get("deliberation_summary", "")
    assert len(summary.split()) <= 40
    assert "Daedalus" in summary
    assert "Marie" in summary
    assert "Hypatia" in summary

    # Step 5: Checkpoint 2 (Curriculum Approval Gate)
    gate = create_approval_gate(
        tmp_path,
        slug=slug,
        title="Distributed Consensus Engineering",
        course_data=course_res,
        deliberation_summary=summary,
    )
    assert (tmp_path / ".tc" / "checkpoint.json").is_file()
    assert summary in gate["prompt"]

    # Learner approves curriculum
    resp = handle_gate_response("start", workspace=tmp_path)
    assert resp["ok"] is True
    assert resp["action"] == "start_lesson"
    assert load_checkpoint(tmp_path) is None

    # Step 6: Two-Tier Clean Workspace verification
    course_dir = tmp_path / "courses" / slug
    root_contents = set(p.name for p in course_dir.iterdir())
    assert root_contents == {"overview.md", "notes", ".tc"}

    tc_dir = course_dir / ".tc"
    assert (tc_dir / "course.toml").is_file()
    assert (tc_dir / "source-map.toml").is_file()
    assert (tc_dir / "consensus-deliberation.md").is_file()
    assert (tc_dir / "memlog.md").is_file()
    assert (tc_dir / "plans").is_dir()

    # Step 7: Lesson delivery and Action Fork verification
    session = get_teaching_session(slug, workspace=tmp_path)
    assert "fork_text" in session
    assert "Next Action Fork" in session["fork_text"]
    assert "[1] Next Concept" in session["fork_text"] or "[1]" in session["fork_text"]
    assert "[2] Test Me" in session["fork_text"] or "[2]" in session["fork_text"]
    assert "[3]" in session["fork_text"]
    assert "[4] Custom" in session["fork_text"] or "[4]" in session["fork_text"]

    # Step 8: Learner advances concept via '1'
    adv = advance_lesson_concept(slug, workspace=tmp_path)
    assert adv["ok"] is True

    # Memory logged to .tc/memlog.md
    memlog_content = (tc_dir / "memlog.md").read_text(encoding="utf-8")
    assert "concept" in memlog_content or "milestone" in memlog_content


def test_strict_zero_bmad_invariant():
    """Verify strictly ZERO occurrences of 'bmad' across all runtime scripts and skills."""
    violations: list[str] = []

    # Check _tc/scripts/
    for py_file in SCRIPTS_DIR.glob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), 1):
            if "bmad" in line.lower():
                violations.append(f"{py_file.name}:{idx} -> {line.strip()}")

    # Check skills/
    for sk_file in SKILLS_DIR.glob("**/*"):
        if sk_file.is_file():
            text = sk_file.read_text(encoding="utf-8", errors="ignore")
            for idx, line in enumerate(text.splitlines(), 1):
                if "bmad" in line.lower():
                    violations.append(f"{sk_file.relative_to(SKILLS_DIR)}:{idx} -> {line.strip()}")

    assert len(violations) == 0, f"Found {len(violations)} Zero-BMad violations:\n" + "\n".join(violations)
