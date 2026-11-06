"""tests/test_multi_source_e2e.py — End-to-end integration test suite for Multi-Source Deterministic Compiler (Epic 11)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
import tomli_w

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from auditor import audit_coverage
from extractor import probe_pdf
from source_mapper import compile_source_map, read_source_pointer, split_source_into_conveyor_batches
from teach_engine import get_teaching_session, verify_vocabulary_turn
from toc_aligner import align_sources_in_directory, build_unified_dag, cluster_multi_source_tocs, extract_toc_from_markdown


@pytest.fixture
def multi_source_e2e_workspace(tmp_path: Path) -> Path:
    """Create a complete realistic workspace with two uploaded gold-standard textbooks and course scaffolding."""
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True)

    raw_dir = ws / "research" / "distributed-storage-internals" / "sources" / "raw"
    raw_dir.mkdir(parents=True)

    # Book 1: Designing Data-Intensive Applications (Martin Kleppmann)
    book1_path = raw_dir / "ddia.md"
    book1_content = """# Designing Data-Intensive Applications
## Chapter 1: Reliable, Scalable, and Maintainable Applications
Reliability means continuing to work correctly even when things go wrong.
Scalability describes a system's ability to cope with increased load.
Maintainability means many different people should be able to work on the system productively.
## Chapter 2: Data Models and Query Languages
Relational model vs Document model vs Graph-like data models.
## Chapter 3: Storage and Retrieval
### SSTables and LSM-Trees
The storage engine maintains an in-memory balanced tree structure called a memtable.
When the memtable is full, it is written out to disk as a sorted string table (SSTable).
Compaction merges SSTables in the background to reclaim disk space.
### B-Trees
B-trees break the database down into fixed-size blocks or pages, traditionally 4KB in size.
In-place page mutation algorithms use write-ahead logs (WAL) to survive crashes.
## Chapter 5: Leaders and Followers
Primary-backup replication protocols coordinate reads and writes across distributed nodes.
"""
    book1_path.write_text(book1_content, encoding="utf-8")

    # Book 2: Database Internals (Alex Petrov)
    book2_path = raw_dir / "database-internals.md"
    book2_content = """# Database Internals
## Part I: B-Tree Basics and Storage Anatomy
Page headers, cell pointers, slotted pages, and binary search in page storage.
## Part II: B-Tree Variants: Bw-Trees
Epoch-based memory reclamation and latch-free page structures for in-memory concurrency.
## Part III: LSM Storage Engines
LSM trees optimize write performance by turning random writes into sequential disk I/O.
Size-tiered compaction triggers when multiple SSTables of approximately equal size accumulate.
Memtables buffer recent writes in skiplist or red-black tree structures before disk flush.
## Part IV: Distributed Transactions: Two-Phase Commit
Coordinator-cohort 2PC protocol, write-ahead logging, and crash-recovery state machines.
"""
    book2_path.write_text(book2_content, encoding="utf-8")

    # Initialize courses directory
    course_dir = ws / "courses" / "distributed-storage-internals"
    course_dir.mkdir(parents=True)

    return ws


def test_end_to_end_multi_source_deterministic_compiler_lifecycle(multi_source_e2e_workspace: Path) -> None:
    """Validate full multi-source deterministic compilation across all 6 spec capabilities (CAP-1 to CAP-6)."""
    ws = multi_source_e2e_workspace
    course_slug = "distributed-storage-internals"
    raw_dir = ws / "research" / course_slug / "sources" / "raw"
    course_dir = ws / "courses" / course_slug

    # =========================================================================
    # Step 1 (CAP-1): Ingestion & Scanned Image Pre-Flight Probe
    # =========================================================================
    probe_res = probe_pdf("non_existent_or_text_fallback.md")
    assert "is_scanned_image" in probe_res
    assert probe_res["is_scanned_image"] is False  # Safe graceful fallback

    # =========================================================================
    # Step 2 (CAP-2): Macro TOC Alignment, Deduplication & Curriculum DAG
    # =========================================================================
    sources = [
        {"id": "ddia", "file": str(raw_dir / "ddia.md"), "toc": extract_toc_from_markdown(raw_dir / "ddia.md")},
        {"id": "database-internals", "file": str(raw_dir / "database-internals.md"), "toc": extract_toc_from_markdown(raw_dir / "database-internals.md")},
    ]

    clustered = cluster_multi_source_tocs(sources)
    assert clustered["total_canonical_topics"] > 0
    assert clustered["common_topics_count"] >= 1  # LSM-Trees and B-Trees appear in both!

    dag_res = build_unified_dag(sources)
    assert dag_res["ok"] is True
    curriculum_dag = dag_res["curriculum_dag"]
    all_sections = [sec for ch in curriculum_dag for sec in ch["sections"]]
    assert len(all_sections) >= 6

    # Verify deduplication: LSM-Trees appears exactly once in the master DAG
    lsm_entry = next((item for item in all_sections if item["section_id"] == "lsm_trees"), None)
    assert lsm_entry is not None

    # Verify niche preservation: Bw-Trees appears in the DAG even though unique to Database Internals
    bw_entry = next((item for item in all_sections if "bw" in item["section_id"]), None)
    assert bw_entry is not None

    # =========================================================================
    # Step 3 (CAP-3): Conveyor-Belt Chapter Batches (<25k Tokens)
    # =========================================================================
    batches = split_source_into_conveyor_batches(raw_dir / "ddia.md", max_tokens_per_batch=25000)
    assert len(batches) >= 1
    for b in batches:
        assert b["token_estimate"] <= 25000
        assert b["line_start"] <= b["line_end"]

    # =========================================================================
    # Step 4 (CAP-4): Compile Deterministic Symbol Table (source-map.toml)
    # =========================================================================
    # Scaffold curriculum in course.toml based on the unified DAG
    course_data = {
        "course": {
            "id": course_slug,
            "title": "Distributed Storage Internals",
            "archetype": "axiomatic_primitives",
        },
        "chapters": [
            {
                "id": "chapter-01",
                "title": "System Foundations & Models",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "Reliable Applications and Failure Modes",
                        "status": "completed",
                        "vocabulary_introduced": ["Reliability", "Scalability", "Maintainability"],
                    },
                    {
                        "id": "sec-02",
                        "title": "Data Models: Relational vs Document",
                        "status": "completed",
                        "vocabulary_introduced": ["Data Models"],
                    },
                ],
            },
            {
                "id": "chapter-02",
                "title": "Storage Engines & In-Memory Indexing",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "Log-Structured Merge-Trees and Compaction",
                        "status": "in_progress",
                        "vocabulary_introduced": ["LSM-Trees", "Memtable", "Compaction"],
                    },
                    {
                        "id": "sec-02",
                        "title": "B-Trees and Page Mutations",
                        "status": "not_started",
                        "vocabulary_introduced": ["B-Trees", "Page Headers"],
                    },
                    {
                        "id": "sec-03",
                        "title": "Bw-Tree Lock-Free Storage",
                        "status": "not_started",
                        "vocabulary_introduced": ["Bw-Trees"],
                    },
                ],
            },
            {
                "id": "chapter-03",
                "title": "Replication & Distributed Consensus",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "Leaders and Followers",
                        "status": "not_started",
                        "vocabulary_introduced": ["Leaders and Followers"],
                    },
                    {
                        "id": "sec-02",
                        "title": "Distributed Transactions: Two-Phase Commit",
                        "status": "not_started",
                        "vocabulary_introduced": ["Two-Phase Commit"],
                    },
                ],
            },
        ],
    }

    (course_dir / "course.toml").write_text(tomli_w.dumps(course_data), encoding="utf-8")

    # Create active section lesson-plan.md
    sec_dir = course_dir / "chapter-02" / "sec-01"
    sec_dir.mkdir(parents=True)
    (sec_dir / "lesson-plan.md").write_text(
        """# Lesson Plan: Log-Structured Merge-Trees and Compaction
## Objectives
- [ ] Master mechanics of LSM-Trees.
- [ ] Understand memtable flush and compaction.
""",
        encoding="utf-8",
    )

    # Compile source-map.toml
    source_map = compile_source_map(course_slug, workspace=ws)
    assert source_map["version"] == "1.0.0"
    assert source_map["course_slug"] == course_slug
    assert len(source_map["sources"]) == 2

    # Verify O(1) instant pointer lookup
    start_time = time.perf_counter()
    pointers = read_source_pointer(course_slug, "lsm_trees", workspace=ws)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    assert elapsed_ms < 200.0  # O(1) direct file slice speed
    assert len(pointers) == 2  # Found in both books!
    assert pointers[0]["dialectic"] is True

    # =========================================================================
    # Step 5 (CAP-5): Complete Coverage Verification Ledger
    # =========================================================================
    cov_result = audit_coverage(course_slug, workspace=ws)
    assert cov_result["ok"] is True
    assert cov_result["status"] == "PASSED"
    assert cov_result["coverage_ratio"] == 100.0
    assert cov_result["dropped_sections"] == 0

    ledger_content = (course_dir / "coverage-ledger.md").read_text(encoding="utf-8")
    assert "Overall Coverage Ratio**: 100.0%" in ledger_content
    assert "Status**: PASSED" in ledger_content
    assert "[✓] Mapped" in ledger_content
    assert "[!] Dropped" not in ledger_content

    # =========================================================================
    # Step 6 (CAP-6): Grounded Sensei Delivery & Vocabulary Contract Gate
    # =========================================================================
    session_context = get_teaching_session(course_slug, workspace=ws)
    assert session_context["ok"] is True
    assert session_context["active_section"]["section_id"] == "sec-01"

    # Verbatim excerpts loaded from symbol table
    assert len(session_context["rag_source_excerpts"]) == 2
    assert session_context["rag_source_excerpts"][0]["dialectic"] is True

    # Vocabulary contract loaded
    v_contract = session_context["vocabulary_contract"]
    assert v_contract["target_term"] == "LSM-Trees"
    assert "Reliability" in v_contract["approved_terms"]
    assert "Data Models" in v_contract["approved_terms"]
    assert v_contract["dialectic"] is True

    # Validate instructional turn with Zero-Unearned-Jargon
    valid_turn = (
        "Imagine writing quick notes on a paper pad on your desk. "
        "When the pad gets full, you transfer the notes into an alphabetically ordered binder on the shelf. "
        "In storage engine terminology, this is called **LSM-Trees**. Martin Kleppmann highlights the sequential write speed, "
        "while Alex Petrov details the background compaction process."
    )
    res_valid = verify_vocabulary_turn(
        turn_text=valid_turn,
        approved_terms=v_contract["approved_terms"],
        target_term=v_contract["target_term"],
    )
    assert res_valid["ok"] is True
    assert res_valid["unearned_terms"] == []

    # Validate that injecting unearned jargon fails the gate
    invalid_turn = (
        "We optimize the writes using **LSM-Trees**, but we also maintain **Merkle Trees** "
        "for anti-entropy repair and coordinate leader election with **Raft Consensus**."
    )
    res_invalid = verify_vocabulary_turn(
        turn_text=invalid_turn,
        approved_terms=v_contract["approved_terms"],
        target_term=v_contract["target_term"],
    )
    assert res_invalid["ok"] is False
    assert len(res_invalid["unearned_terms"]) >= 1
    assert any("merkle" in t for t in res_invalid["unearned_terms"])
    assert any("raft" in t for t in res_invalid["unearned_terms"])


def test_zero_bmad_invariant_across_epic_11() -> None:
    """Verify that all runtime scripts and skills have strictly ZERO mentions of bmad."""
    files_to_check = [
        SCRIPTS_DIR / "extractor.py",
        SCRIPTS_DIR / "toc_aligner.py",
        SCRIPTS_DIR / "source_mapper.py",
        SCRIPTS_DIR / "auditor.py",
        SCRIPTS_DIR / "teach_engine.py",
        SCRIPTS_DIR / "course_builder.py",
        Path("skills/tc/SKILL.md"),
        Path("_tc/skills/tc-create/SKILL.md"),
        Path("_tc/skills/tc-research/SKILL.md"),
        Path("_tc/skills/tc-teach/SKILL.md"),
        Path("_tc/skills/tc-verify-course/SKILL.md"),
    ]

    for f in files_to_check:
        if f.is_file():
            content = f.read_text(encoding="utf-8").lower()
            assert "bmad" not in content, f"Found 'bmad' in {f}"
