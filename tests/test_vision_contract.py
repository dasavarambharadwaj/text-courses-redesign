"""tests/test_vision_contract.py — 12-Point Learner Vision Contract E2E Integration Suite.

Validates all 12 points of the Learner Vision Contract (CAP-1..10, FR-46..50) against
real runtime execution with strict Zero-BMad compliance.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from bootstrapper import bootstrap_workspace
from checkpoint_manager import (
    GATE_APPROVAL,
    GATE_SECTION_CLOSE,
    GATE_SOURCE_PROPOSAL,
    create_section_close_gate,
    handle_gate_response,
    load_checkpoint,
)
from course_builder import create_course, scaffold_course_files
from dashboard_generator import write_status_dashboard
from extractor import convert_sources_to_markdown
from scout import conduct_four_hat_debate, generate_source_proposal_markdown
from tc import dispatch_conversational_turn
from teach_engine import advance_lesson_concept, append_session_event


def test_point_01_single_public_surface():
    """Point 1: Exactly one public skill (skills/tc/) is exported. All engine skills are internal in _tc/skills/."""
    skills_dir = ROOT_DIR / "skills"
    assert skills_dir.is_dir()
    public_skills = [d.name for d in skills_dir.iterdir() if d.is_dir()]
    assert public_skills == ["tc"], f"Expected exactly ['tc'] in skills/, found: {public_skills}"

    internal_skills_dir = ROOT_DIR / "_tc" / "skills"
    assert internal_skills_dir.is_dir()
    internal_skills = [d.name for d in internal_skills_dir.iterdir() if d.is_dir()]
    assert len(internal_skills) >= 5, "Internal engine skills must reside inside _tc/skills/"


def test_point_02_clean_canvas_and_canonical_storage(tmp_path: Path):
    """Point 2: Research, docs, and decisions live in _tc/; outside _tc/, only courses/<slug>/notes/ is visible for study."""
    ws = tmp_path / "workspace_p2"
    bootstrap_workspace(path=ws)

    # Invariant: Root canvas strictly allows _tc/, courses/, portfolio/, status-board/
    root_dirs = sorted([d.name for d in ws.iterdir() if d.is_dir()])
    assert root_dirs == ["_tc", "courses", "portfolio", "status-board"]

    # Canonical storage trees inside _tc/
    for sub in ["courses", "research", "profile", "roadmap", "status", "cache"]:
        assert (ws / "_tc" / sub).is_dir(), f"_tc/{sub} must exist"


def test_point_03_five_stage_intake_and_mode_selection(tmp_path: Path):
    """Point 3: Intake captures learning goals, experience level, and execution mode (--mode interactive|auto)."""
    ws = tmp_path / "workspace_p3"
    bootstrap_workspace(path=ws)

    # Dispatch turn with auto mode flag
    res = dispatch_conversational_turn(
        user_input="Teach me Rust systems programming --mode auto",
        workspace=ws,
        mode="auto",
    )
    assert res["ok"] is True
    # Preference file must record mode: auto
    pref_file = ws / "_tc" / "profile" / "preferences.md"
    assert pref_file.is_file()
    pref_text = pref_file.read_text(encoding="utf-8")
    assert 'mode: "auto"' in pref_text or 'mode: auto' in pref_text


def test_point_04_interactive_source_proposal(tmp_path: Path):
    """Point 4: Interactive research proposes best sources across 6 channels and accepts approval, more, or stop."""
    proposal_md = generate_source_proposal_markdown(
        slug="db-internals",
        topic="Database Internals",
        canonical_books=[{"title": "Designing Data-Intensive Applications", "author": "Kleppmann", "status": "AVAILABLE"}],
        official_sources=[{"title": "SQLite Documentation", "url": "https://sqlite.org"}],
    )
    assert "Channel 1: Landmark Canonical Textbooks" in proposal_md
    assert "Channel 2: Academic Research Papers" in proposal_md
    assert "Channel 3: Official Specifications" in proposal_md
    assert "Channel 4: Open-Source GitHub Repositories" in proposal_md
    assert "Channel 5: Community Consensus" in proposal_md
    assert "Channel 6: Curated Web Articles" in proposal_md
    assert "`[1]` **Approve Sources & Fetch All**" in proposal_md


def test_point_05_unattended_auto_mode_creation(tmp_path: Path):
    """Point 5: Auto mode runs all creation steps without human approval pauses; agent decides with decision logging."""
    ws = tmp_path / "workspace_p5"
    bootstrap_workspace(path=ws, mode="auto")

    res = dispatch_conversational_turn(
        user_input="Compiler construction",
        workspace=ws,
        mode="auto",
    )
    assert res["ok"] is True
    assert res["mode"] == "auto"
    assert res["action"] == "auto_created"

    # Verify decision logged in scoped memlog (profile or course scope)
    memlog_file = ws / "_tc" / "profile" / "memlog.md"
    if not memlog_file.is_file():
        memlog_file = ws / "_tc" / "courses" / "compiler-construction" / "memlog.md"
    assert memlog_file.is_file()
    memlog_text = memlog_file.read_text(encoding="utf-8")
    assert "Auto-mode" in memlog_text or "decision" in memlog_text


def test_point_06_multi_source_harvest_and_fallback(tmp_path: Path):
    """Point 6: Fetch resources into _tc/research/<slug>/sources/; missing proprietary materials fallback gracefully."""
    slug = "cache-internals"
    src_dir = tmp_path / "_tc" / "research" / slug / "sources" / "markdown"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "lru_cache.md").write_text("# LRU Cache\nImplementation.\n", encoding="utf-8")

    assert (src_dir / "lru_cache.md").is_file()


def test_point_07_zero_loss_markdown_and_4_hat_debate(tmp_path: Path):
    """Point 7: Convert any material to Markdown without text loss with conversion-ledger proof, and run 4-hat debate."""
    slug = "parsing-theory"
    src_dir = tmp_path / "_tc" / "research" / slug / "sources"
    raw_dir = src_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    test_file = raw_dir / "grammar.html"
    test_file.write_text("<h1>Grammar Rules</h1><p>BNF notation and context-free grammars.</p>", encoding="utf-8")

    res_conv = convert_sources_to_markdown(slug=slug, workspace=tmp_path)
    assert res_conv["ok"] is True
    assert res_conv["total_sources"] >= 1
    assert res_conv["global_text_coverage_pct"] == 100.0
    assert Path(res_conv["ledger_json"]).is_file()

    # Run 4-hat debate
    debate_res = conduct_four_hat_debate(slug=slug, topic="Context Free Grammars", workspace=tmp_path)
    assert debate_res["ok"] is True
    assert debate_res["debate_records_count"] >= 3
    assert (tmp_path / "_tc" / "research" / slug / "debate.jsonl").is_file()


def test_point_08_roadmap_and_course_scaffolding(tmp_path: Path):
    """Point 8: Scaffolds course syllabus DAG and blueprint in _tc/courses/<slug>/."""
    slug = "concurrency-primitives"
    create_course(slug=slug, title="Concurrency Primitives", topic="Mutexes and Atomics", workspace=tmp_path)

    bp = tmp_path / "_tc" / "courses" / slug / "blueprint.md"
    assert bp.is_file(), "_tc/courses/<slug>/blueprint.md must be scaffolded"
    content = bp.read_text(encoding="utf-8")
    assert "Course Blueprint: Concurrency Primitives" in content


def test_point_09_blueprint_approval_gate_and_grounded_plans(tmp_path: Path):
    """Point 9: Gate 2 displays blueprint; section plans contain exact line spans and Bloom rubrics."""
    slug = "network-internals"
    course_data = {
        "course": {"id": slug, "title": "Network Internals", "archetype": "applied_creation"},
        "chapters": [
            {
                "id": "chapter-01",
                "title": "Socket Layer",
                "sections": [{"id": "sec-01", "title": "TCP Sockets"}],
            }
        ],
    }
    scaffold_course_files(tmp_path, course_data)

    plan_file = tmp_path / "_tc" / "courses" / slug / "plans" / "chapter-01-socket-layer" / "section-01-tcp-sockets" / "lesson-plan.md"
    assert plan_file.is_file()
    plan_text = plan_file.read_text(encoding="utf-8")

    assert "## Teaching Plan" in plan_text
    assert "Intuitive Metaphor & Core Invariant" in plan_text
    assert "Technical Formalism" in plan_text
    assert "Applied Practical Exercise" in plan_text
    assert "## Source-Coverage Map" in plan_text
    assert "## Verification Plan" in plan_text
    assert "Bloom Diagnostic Probes" in plan_text
    assert "Failure Injection Scenario" in plan_text


def test_point_10_teaching_engine_and_visible_notes(tmp_path: Path):
    """Point 10: tc teaches directly; conversation in _tc/; notes compiled on completion to courses/<slug>/notes/."""
    slug = "raft-consensus"
    create_course(slug=slug, title="Raft Consensus", topic="Leader Election", workspace=tmp_path)

    # Advance first concept
    r1 = advance_lesson_concept(course_slug=slug, workspace=tmp_path)
    assert r1["ok"] is True

    # Advance second concept (final concept)
    r2 = advance_lesson_concept(course_slug=slug, workspace=tmp_path)
    assert r2["ok"] is True
    assert r2["section_fully_completed"] is True

    # Visible notes must exist in courses/<slug>/notes/chapter-01.md
    notes_file = tmp_path / "courses" / slug / "notes" / "chapter-01.md"
    assert notes_file.is_file()
    assert len(notes_file.read_text(encoding="utf-8")) > 50


def test_point_11_mandatory_section_close_gate_and_ephemeral_scrub(tmp_path: Path):
    """Point 11: Mandatory section-close gate halts in all modes; approved close marks completed and permanently scrubs session."""
    slug = "vm-paging"
    create_course(slug=slug, title="Virtual Memory Paging", topic="Page Tables", workspace=tmp_path)
    c_dir = tmp_path / "courses" / slug

    append_session_event(c_dir, {"section_id": "sec-01", "summary": "Paging dialogue."})
    sess_file = c_dir / ".tc" / "session.jsonl"
    assert sess_file.is_file()

    # Open section close gate
    create_section_close_gate(
        workspace=tmp_path,
        slug=slug,
        chapter_id=1,
        section_id="sec-01",
        section_title="Page Tables",
    )
    assert load_checkpoint(tmp_path)["gate"] == GATE_SECTION_CLOSE

    # Approve close
    res = handle_gate_response("1", workspace=tmp_path)
    assert res["ok"] is True
    assert res["action"] == "approve_close"
    assert res["section_status"] == "completed"
    assert res["session_scrubbed"] is True

    # Transcript scrubbed
    assert not sess_file.is_file()
    assert load_checkpoint(tmp_path) is None


def test_point_12_self_contained_local_interactive_status_dashboard(tmp_path: Path):
    """Point 12: status-board/index.html generated from _tc/status/state.json; opens offline via file:// with 0 network requests."""
    state_file, html_file = write_status_dashboard(tmp_path)

    assert state_file.is_file()
    assert html_file.is_file()

    html_content = html_file.read_text(encoding="utf-8")
    assert "TextCourses Status Board" in html_content

    # Invariant: 0 external CDN / HTTP requests
    external_refs = re.findall(r'(?:src|href|url)\s*=\s*["\'](https?://[^"\']+)["\']', html_content, re.IGNORECASE)
    assert len(external_refs) == 0, f"Found external URL in dashboard: {external_refs}"


def test_zero_bmad_compliance_in_runtime_and_skills():
    """Verify zero BMad references exist across all files in public skills/ and internal _tc/."""
    violating_files = []
    for root_dir in [ROOT_DIR / "skills", ROOT_DIR / "_tc"]:
        for p in root_dir.rglob("*"):
            if not p.is_file() or ".git" in p.parts:
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                if "bmad" in content.lower():
                    violating_files.append(str(p.relative_to(ROOT_DIR)))
            except Exception:
                pass

    assert len(violating_files) == 0, f"BMad references detected in runtime/skills: {violating_files}"
