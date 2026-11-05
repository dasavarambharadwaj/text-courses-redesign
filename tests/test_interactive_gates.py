"""tests/test_interactive_gates.py — Verification of Interactive Checkpoint Gates & Acquisition Pause (CAP-2)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from checkpoint_manager import (
    GATE_ACQUISITION,
    GATE_APPROVAL,
    clear_checkpoint,
    create_acquisition_gate,
    create_approval_gate,
    handle_gate_response,
    load_checkpoint,
)


def create_mock_pdf(path: Path) -> Path:
    """Create a minimal valid digital PDF."""
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
<< /Length 75 >>
stream
BT
/F1 12 Tf
72 712 Td
(Distributed Systems Architecture) Tj
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
0000000370 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
450
%%EOF"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw_pdf)
    return path


def test_create_and_load_acquisition_gate(tmp_path: Path):
    """Verify acquisition gate pauses and generates clear options when books are missing."""
    gate = create_acquisition_gate(
        workspace=tmp_path,
        slug="storage-internals",
        recommended_books=["Designing Data-Intensive Applications", "Database Internals"],
    )
    assert gate["gate"] == GATE_ACQUISITION
    assert (tmp_path / ".tc" / "checkpoint.json").is_file()

    loaded = load_checkpoint(tmp_path)
    assert loaded is not None
    assert loaded["gate"] == GATE_ACQUISITION
    assert "Designing Data-Intensive Applications" in loaded["prompt"]
    assert "`[1]` **Proceed with Open Docs**" in loaded["prompt"]
    assert "`[2]` **I'll Drop Files**" in loaded["prompt"]


def test_acquisition_gate_response_proceed_open(tmp_path: Path):
    """Verify selecting option 1 clears acquisition gate and proceeds with open documentation."""
    create_acquisition_gate(
        workspace=tmp_path,
        slug="storage-internals",
        recommended_books=["Designing Data-Intensive Applications"],
    )

    res = handle_gate_response("1", workspace=tmp_path)
    assert res["ok"] is True
    assert res["has_active_gate"] is False
    assert res["action"] == "proceed_open"
    assert load_checkpoint(tmp_path) is None


def test_acquisition_gate_detects_new_dropped_file(tmp_path: Path):
    """Verify dropping a book into workspace automatically clears acquisition pause."""
    create_acquisition_gate(
        workspace=tmp_path,
        slug="storage-internals",
        recommended_books=["Designing Data-Intensive Applications"],
        found_sources=[],
    )

    # Drop textbook into workspace
    create_mock_pdf(tmp_path / "books" / "ddia.pdf")

    res = handle_gate_response("I added the book", workspace=tmp_path)
    assert res["ok"] is True
    assert res["has_active_gate"] is False
    assert res["action"] == "files_detected"
    assert len(res["new_files"]) >= 1


def test_create_and_handle_approval_gate(tmp_path: Path):
    """Verify approval gate presents roadmap and deliberation summary and responds to user choices."""
    course_data = {
        "chapters": [
            {
                "title": "Storage Foundations",
                "sections": [{"title": "LSM-Trees"}, {"title": "B-Trees"}],
            },
            {
                "title": "Distributed Consensus",
                "sections": [{"title": "Raft Basics"}, {"title": "Two-Phase Commit"}],
            },
        ]
    }
    delib_summary = "🏛️ Daedalus, 🔬 Marie, and ⚖️ Hypatia synthesized a 2-chapter, 4-section curriculum with 100% coverage."

    gate = create_approval_gate(
        workspace=tmp_path,
        slug="dist-db",
        title="Distributed Databases",
        course_data=course_data,
        deliberation_summary=delib_summary,
    )
    assert gate["gate"] == GATE_APPROVAL
    assert "Storage Foundations" in gate["prompt"]
    assert "Distributed Consensus" in gate["prompt"]
    assert delib_summary in gate["prompt"]

    # Option 1: Start lesson
    res_start = handle_gate_response("start", workspace=tmp_path)
    assert res_start["ok"] is True
    assert res_start["has_active_gate"] is False
    assert res_start["action"] == "start_lesson"

    # Option 2: Suggest adjustment
    create_approval_gate(
        workspace=tmp_path,
        slug="dist-db",
        title="Distributed Databases",
        course_data=course_data,
        deliberation_summary=delib_summary,
    )
    res_adj = handle_gate_response("Can we add a section on Paxos in chapter 2?", workspace=tmp_path)
    assert res_adj["ok"] is True
    assert res_adj["action"] == "reconcile_adjustment"
    assert "Paxos" in res_adj["adjustment"]


def test_checkpoint_manager_cli(tmp_path: Path):
    """Verify checkpoint_manager CLI commands (status, respond, clear)."""
    cp_script = SCRIPTS_DIR / "checkpoint_manager.py"

    create_acquisition_gate(
        workspace=tmp_path,
        slug="cli-test",
        recommended_books=["Compilers: Principles, Techniques, and Tools"],
    )

    # 1. status
    res_stat = subprocess.run(
        [sys.executable, str(cp_script), "status", "--workspace", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
    )
    assert res_stat.returncode == 0
    stat_data = json.loads(res_stat.stdout)
    assert stat_data["active_checkpoint"]["gate"] == GATE_ACQUISITION

    # 2. respond
    res_resp = subprocess.run(
        [sys.executable, str(cp_script), "respond", "--response", "proceed", "--workspace", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
    )
    assert res_resp.returncode == 0
    resp_data = json.loads(res_resp.stdout)
    assert resp_data["action"] == "proceed_open"

    # 3. clear
    create_acquisition_gate(workspace=tmp_path, slug="cli-test-2", recommended_books=["Book A"])
    res_clear = subprocess.run(
        [sys.executable, str(cp_script), "clear", "--workspace", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
    )
    assert res_clear.returncode == 0
    assert load_checkpoint(tmp_path) is None
