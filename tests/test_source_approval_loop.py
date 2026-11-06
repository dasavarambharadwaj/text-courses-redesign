#!/usr/bin/env python3
"""tests/test_source_approval_loop.py — Multi-source discovery, interactive proposal and fallback loop tests (FR-43, CAP-8)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from _tc.scripts import scout, checkpoint_manager, tc, memlog, bootstrapper


def setup_workspace_profile(ws: Path, mode: str = "interactive") -> None:
    """Setup canonical workspace profile with mode."""
    bootstrapper.bootstrap_workspace(path=ws, mode=mode)


def test_scout_generates_source_proposal_across_channels(tmp_path: Path) -> None:
    """Verify scout synthesizes structured 6-channel source proposal markdown under canonical _tc/research/."""
    res = scout.run_scout(
        slug="rust-distributed",
        topic="Rust Distributed Systems",
        workspace=tmp_path,
    )
    assert res["ok"] is True
    canon_proposal = tmp_path / "_tc" / "research" / "rust-distributed" / "source-proposal.md"
    assert canon_proposal.is_file(), "Canonical source-proposal.md missing from _tc/research/"
    
    content = canon_proposal.read_text(encoding="utf-8")
    assert "Multi-Source Research Proposal" in content
    assert "Channel 1: Landmark Canonical Textbooks" in content
    assert "Channel 2: Academic Research Papers" in content
    assert "Channel 3: Official Specifications, Standards & RFCs" in content
    assert "Channel 4: Open-Source GitHub Repositories" in content
    assert "Channel 5: Community Consensus" in content
    assert "Channel 6: Curated Web Articles" in content
    assert "`[1]` **Approve Sources & Fetch All**" in content
    assert "`[2]` **Request More Research**" in content
    assert "`[3]` **Add Custom Source**" in content
    assert "`[4]` **Remove Source**" in content
    assert "`[5]` **Stop**" in content

    digest = res.get("digest", {})
    assert "source_proposal_path" in digest
    assert str(canon_proposal) in digest["source_proposal_path"]


def test_checkpoint_source_proposal_gate_options(tmp_path: Path) -> None:
    """Verify checkpoint manager supports 5-action source proposal gate."""
    # 1. Create gate
    gate = checkpoint_manager.create_source_proposal_gate(
        workspace=tmp_path,
        slug="storage-engine",
        topic="Storage Engines",
        recommended_books=["Designing Data-Intensive Applications"],
        found_sources=["RFC 793"],
    )
    assert gate["gate"] == checkpoint_manager.GATE_SOURCE_PROPOSAL
    assert len(gate["options"]) == 5

    # 2. Test 'more' research inquiry keeps gate active
    res_more = checkpoint_manager.handle_gate_response("more research", workspace=tmp_path)
    assert res_more["has_active_gate"] is True
    assert res_more["action"] == "more_research"

    # 3. Test 'add' custom source keeps gate active
    res_add = checkpoint_manager.handle_gate_response("add: https://github.com/tikv/tikv", workspace=tmp_path)
    assert res_add["has_active_gate"] is True
    assert res_add["action"] == "add_source"
    assert "https://github.com/tikv/tikv" in res_add["custom_source"]

    # 4. Test 'remove' source keeps gate active
    res_rem = checkpoint_manager.handle_gate_response("remove: RFC 793", workspace=tmp_path)
    assert res_rem["has_active_gate"] is True
    assert res_rem["action"] == "remove_source"
    assert "RFC 793" in res_rem["removed_source"]

    # 5. Test 'stop' clears gate
    res_stop = checkpoint_manager.handle_gate_response("stop", workspace=tmp_path)
    assert res_stop["has_active_gate"] is False
    assert res_stop["action"] == "stop"
    assert checkpoint_manager.load_checkpoint(tmp_path) is None

    # 6. Recreate and test '1' / approve clears gate
    checkpoint_manager.create_source_proposal_gate(
        workspace=tmp_path,
        slug="storage-engine",
        topic="Storage Engines",
    )
    res_app = checkpoint_manager.handle_gate_response("1", workspace=tmp_path)
    assert res_app["has_active_gate"] is False
    assert res_app["action"] == "proceed_open"
    assert checkpoint_manager.load_checkpoint(tmp_path) is None


def test_dispatch_source_approval_workflow(tmp_path: Path) -> None:
    """Verify tc dispatch on interactive mode presents proposal gate and advances to blueprint upon approval."""
    setup_workspace_profile(tmp_path, mode="interactive")

    # 1. Initial turn on topic pauses at source proposal / acquisition gate
    turn_1 = tc.dispatch_conversational_turn("Distributed Paxos", workspace=tmp_path)
    assert turn_1["ok"] is True
    assert turn_1["state"] == "acquisition_gate"
    assert turn_1["gate"] == "source_proposal"
    assert "active_artifact" in turn_1
    assert "source-proposal.md" in turn_1["active_artifact"]
    assert Path(turn_1["active_artifact"]).is_file()

    # 2. User approves sources
    turn_2 = tc.dispatch_conversational_turn("1", workspace=tmp_path)
    assert turn_2["ok"] is True
    assert turn_2["state"] == "blueprint"
    assert turn_2["action"] == "proceed_open"
    assert "blueprint.md" in turn_2["active_artifact"]


def test_dispatch_more_research_and_add_source_interaction(tmp_path: Path) -> None:
    """Verify interactive loop handles more research, custom source additions, and halting."""
    setup_workspace_profile(tmp_path, mode="interactive")

    # Initial turn
    tc.dispatch_conversational_turn("Network Protocols", workspace=tmp_path)

    # Learner requests more research
    turn_more = tc.dispatch_conversational_turn("2", workspace=tmp_path)
    assert turn_more["ok"] is True
    assert turn_more["state"] == "acquisition_gate"
    assert turn_more["action"] == "more_research"

    # Learner adds a custom source
    turn_add = tc.dispatch_conversational_turn("add: https://github.com/smoltcp-rs/smoltcp", workspace=tmp_path)
    assert turn_add["ok"] is True
    assert turn_add["state"] == "acquisition_gate"
    assert turn_add["action"] == "add_source"

    # Learner stops
    turn_stop = tc.dispatch_conversational_turn("stop", workspace=tmp_path)
    assert turn_stop["ok"] is True
    assert turn_stop["state"] == "stopped"


def test_material_fallback_logging_in_auto_and_interactive(tmp_path: Path) -> None:
    """Verify material fallback writes non-silent gap entries to scoped memlog without stalling."""
    # 1. Auto mode with proprietary book
    setup_workspace_profile(tmp_path, mode="auto")
    turn_auto = tc.dispatch_conversational_turn("Operating Systems", workspace=tmp_path)
    assert turn_auto["ok"] is True
    assert turn_auto["state"] == "teaching"

    # Verify decision logged in memlog
    prof_log = tmp_path / "_tc" / "profile" / "memlog.md"
    assert prof_log.is_file()
    assert "Auto-mode decision" in prof_log.read_text(encoding="utf-8")

    # 2. Interactive mode approving fallback
    ws_int = tmp_path / "interactive_ws"
    setup_workspace_profile(ws_int, mode="interactive")
    tc.dispatch_conversational_turn("Database Internals", workspace=ws_int)
    turn_int = tc.dispatch_conversational_turn("1", workspace=ws_int)
    assert turn_int["ok"] is True
    assert turn_int["state"] == "blueprint"

    res_log = ws_int / "_tc" / "research" / "database-internals" / "memlog.md"
    assert res_log.is_file()
    content = res_log.read_text(encoding="utf-8")
    assert "Material fallback" in content
    assert "proprietary textbooks" in content
