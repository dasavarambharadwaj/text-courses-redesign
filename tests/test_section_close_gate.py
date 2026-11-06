"""tests/test_section_close_gate.py — Tests for Mandatory Section-Close Gate, Visible Notes & Ephemeral Session Scrub (CAP-6, CAP-9, FR-11, FR-49)."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from checkpoint_manager import (
    GATE_SECTION_CLOSE,
    approve_section_close,
    create_section_close_gate,
    handle_gate_response,
    load_checkpoint,
)
from course_builder import create_course
from teach_engine import advance_lesson_concept, append_session_event
from tc import dispatch_conversational_turn


def test_section_completion_triggers_section_close_gate(tmp_path: Path):
    """Verify that completing all concepts opens mandatory section close gate and compiles visible notes."""
    slug = "os-internals"
    create_course(slug=slug, title="Operating Systems Internals", topic="Virtual Memory and Paging", workspace=tmp_path)

    # Add a mock session event to verify ephemeral transcript is written
    c_dir = tmp_path / "courses" / slug
    append_session_event(c_dir, {"section_id": "sec-01", "summary": "Discussed page tables and TLBs."})
    sess_file = c_dir / ".tc" / "session.jsonl"
    assert sess_file.is_file(), "Ephemeral session transcript must exist during active teaching"

    # Advance concept 1
    r1 = advance_lesson_concept(course_slug=slug, workspace=tmp_path)
    assert r1["ok"] is True
    assert r1.get("gate") is None

    # Advance concept 2 (final concept)
    r2 = advance_lesson_concept(course_slug=slug, workspace=tmp_path)
    assert r2["ok"] is True
    assert r2["section_fully_completed"] is True
    assert r2.get("gate") == GATE_SECTION_CLOSE
    assert r2.get("has_active_gate") is True

    # Checkpoint gate must be active
    cp = load_checkpoint(tmp_path)
    assert cp is not None
    assert cp["gate"] == GATE_SECTION_CLOSE
    assert cp["slug"] == slug
    assert "Section Sign-Off Gate" in cp["prompt"]
    assert "`[1]` **Approve & Close Section**" in cp["prompt"]
    assert "`[2]` **Revise Notes**" in cp["prompt"]
    assert "`[3]` **Re-explain / Deepen**" in cp["prompt"]
    assert "`[4]` **Keep Session Open**" in cp["prompt"]

    # Visible notes must exist in courses/<slug>/notes/chapter-01.md (CAP-6)
    notes_file = tmp_path / "courses" / slug / "notes" / "chapter-01.md"
    assert notes_file.is_file(), "Visible notes must exist at courses/<slug>/notes/chapter-01.md"
    assert len(notes_file.read_text(encoding="utf-8")) > 50


def test_section_close_gate_options_interaction(tmp_path: Path):
    """Verify Section Close Gate responds to revise notes, deepen, and keep open."""
    slug = "compiler-basics"
    create_section_close_gate(
        workspace=tmp_path,
        slug=slug,
        chapter_id=1,
        section_id="sec-01",
        section_title="Lexical Tokens",
        recap=["Token stream abstraction", "Regular expressions"],
    )

    # Option 2: Revise notes
    res_rev = handle_gate_response("2", workspace=tmp_path)
    assert res_rev["ok"] is True
    assert res_rev["has_active_gate"] is True
    assert res_rev["action"] == "revise_notes"

    # Option 3: Deepen
    res_deep = handle_gate_response("3", workspace=tmp_path)
    assert res_deep["ok"] is True
    assert res_deep["has_active_gate"] is True
    assert res_deep["action"] == "deepen"

    # Option 4: Keep session open
    res_keep = handle_gate_response("4", workspace=tmp_path)
    assert res_keep["ok"] is True
    assert res_keep["has_active_gate"] is True
    assert res_keep["action"] == "keep_open"


def test_approve_section_close_scrubs_session_and_updates_status(tmp_path: Path):
    """Verify approval transitions section to completed, updates memlog, and permanently scrubs session transcript (CAP-9, FR-49)."""
    slug = "network-protocols"
    create_course(slug=slug, title="Network Protocols", topic="TCP and Congestion Control", workspace=tmp_path)

    c_dir = tmp_path / "courses" / slug
    append_session_event(c_dir, {"section_id": "sec-01", "summary": "Three-way handshake breakdown."})
    sess_file = c_dir / ".tc" / "session.jsonl"
    assert sess_file.is_file()

    # Create dummy visible chapter notes
    notes_dir = c_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    (notes_dir / "chapter-01.md").write_text("# Chapter 01 Notes\n\nTCP Handshake mechanics.\n", encoding="utf-8")

    # Open section close gate
    create_section_close_gate(
        workspace=tmp_path,
        slug=slug,
        chapter_id=1,
        section_id="sec-01",
        section_title="TCP Handshake",
        recap=["SYN, SYN-ACK, ACK handshake sequence", "Sequence number synchronization"],
    )

    # Learner approves and closes section
    res_close = handle_gate_response("1", workspace=tmp_path)
    assert res_close["ok"] is True
    assert res_close["has_active_gate"] is False
    assert res_close["action"] == "approve_close"
    assert res_close["section_status"] == "completed"
    assert res_close["session_scrubbed"] is True
    assert res_close["notes_verified"] is True

    # 1. Ephemeral session transcript must be deleted (permanently scrubbed)
    assert not sess_file.is_file(), "session.jsonl must be unlinked/scrubbed upon section close approval"

    # 2. Section status in course.toml must be 'completed'
    c_toml = c_dir / ".tc" / "course.toml"
    with open(c_toml, "r", encoding="utf-8") as f:
        content = f.read()
    assert 'status = "completed"' in content

    # 3. Scoped memlogs appended
    memlog_file = tmp_path / "_tc" / "courses" / slug / "memlog.md"
    if not memlog_file.is_file():
        memlog_file = c_dir / ".tc" / "memlog.md"
    assert memlog_file.is_file()
    assert "completed" in memlog_file.read_text(encoding="utf-8")

    # 4. Gate checkpoint cleared
    assert load_checkpoint(tmp_path) is None


def test_tc_dispatch_handles_section_close_approval(tmp_path: Path):
    """Verify tc.py run_dispatch seamlessly approves section close when gate is pending."""
    slug = "db-internals"
    create_course(slug=slug, title="Database Internals", topic="Storage and B-Trees", workspace=tmp_path)
    c_dir = tmp_path / "courses" / slug

    notes_dir = c_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    (notes_dir / "chapter-01.md").write_text("# Chapter 01 Notes\n", encoding="utf-8")

    create_section_close_gate(
        workspace=tmp_path,
        slug=slug,
        chapter_id=1,
        section_id="sec-01",
        section_title="B-Tree Invariants",
    )

    # Call dispatch with '1' (Approve close)
    res = dispatch_conversational_turn(user_input="1", workspace=tmp_path)
    assert res["ok"] is True
    assert res["state"] == "section_closed"
    assert res["action"] == "approve_close"
    assert res["session_scrubbed"] is True
    assert res["notes_verified"] is True
    assert load_checkpoint(tmp_path) is None
