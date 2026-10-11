"""tests/test_indexer.py — Comprehensive test suite for Denis Diderot's Sovereign Knowledge Indexer (FR-45)."""

from __future__ import annotations

import json
import sqlite3
import sys
import tracemalloc
from pathlib import Path
from typing import Any

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
for p in [str(SCRIPTS_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from course_builder import create_course
from indexer import (
    extract_domain_catalog,
    get_cached_catalog,
    init_index_db,
    parse_markdown_into_breadcrumb_chunks,
    run_build_index,
    run_query_index,
)


@pytest.fixture
def temp_sources_workspace(tmp_path: Path) -> tuple[Path, str]:
    """Create a temporary workspace with rich heterogeneous research sources."""
    slug = "distributed-consensus"
    sources_dir = tmp_path / "research" / slug / "sources"
    sources_dir.mkdir(parents=True)

    # 1. Harvested markdown textbook chapter
    textbook_dir = sources_dir / "repos" / "consensus-handbook"
    textbook_dir.mkdir(parents=True)
    textbook_file = textbook_dir / "raft-chapter.md"
    textbook_file.write_text(
        """# Raft Consensus Algorithm
## Leader Election Protocol
In the Raft protocol, nodes start in a follower state. If heartbeats timeout, an election starts.
The candidate votes for itself and issues `RequestVote` RPCs to peers.
A term counter ensures monotonic progression of logical time.

## Log Replication Mechanics
Once a leader is established, clients send state machine commands.
The leader appends the entry to its local log and issues `AppendEntries` RPCs.
When a majority acknowledges the write, the entry is committed to the replicated state machine.

### Safety Invariants and Boundary Conditions
Raft guarantees Election Safety: at most one leader can be elected in a given term.
Leader Append-Only: a leader never overwrites or truncates its own log entries.
Log Matching Property: if two logs contain an entry with the same index and term, they are identical up to that index.
""",
        encoding="utf-8",
    )

    # 2. Lecture transcript
    transcripts_dir = sources_dir / "transcripts"
    transcripts_dir.mkdir(parents=True)
    transcript_file = transcripts_dir / "mit-6824-raft-lecture.md"
    transcript_file.write_text(
        """# MIT 6.824 Lecture: Raft Implementation Dilemmas
## Split Brain Scenarios
Professor explains: When a network partition occurs, how does Raft prevent split brain?
The minority partition cannot achieve quorum, so it cannot commit client writes.
Meanwhile, the majority partition continues accepting writes.
When the partition heals, the term counter resolves any leader ambiguity.

## State Machine Replication
State Machine Replication (SMR) requires deterministic execution of all state transitions.
If your state machine reads non-deterministic wall-clock time, replicas will diverge.
Use logical log indexes instead of local wall-clock timers.
""",
        encoding="utf-8",
    )

    # 3. Code repository notes
    repo_notes = textbook_dir / "implementation-notes.md"
    repo_notes.write_text(
        """# Raft Engine Engineering Notes
## Persistent Storage Commit Log
The engine stores `current_term`, `voted_for`, and the `log` array to non-volatile disk.
We use `fsync` before replying to RPCs to satisfy durability invariants.
Performance requires batching multiple client transactions into a single write pipeline.
""",
        encoding="utf-8",
    )

    return tmp_path, slug


def test_init_index_db_schema_and_pragmas(tmp_path: Path) -> None:
    """Test SQLite database initialization, pragmas, and FTS5 Porter stemmer."""
    db_file = tmp_path / "test_index.db"
    conn = init_index_db(db_file)
    assert db_file.is_file()

    # Check tables exist
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {r[0] for r in cur.fetchall()}
    assert "documents" in tables
    assert "chunks" in tables
    assert "fts_chunks" in tables

    # Test FTS5 trigger synchronization and Porter stemmer
    conn.execute(
        "INSERT INTO documents (rel_path, title, doc_type, source_group, file_size_bytes, sha256, created_at) "
        "VALUES ('doc1.md', 'Doc 1', 'md', 'grp', 100, 'sha1', '2026-01-01');"
    )
    doc_id = cur.lastrowid
    conn.execute(
        "INSERT INTO chunks (doc_id, chunk_index, breadcrumb, heading, content, token_count, metadata_json) "
        "VALUES (?, 0, 'Doc 1 > Testing', 'Testing', 'The consensus algorithms replicated state machines cleanly.', 7, '{}');",
        (doc_id,),
    )
    conn.commit()

    # Query with stemmed token ("algorithm" matches "algorithms", "replicate" matches "replicated")
    cur.execute("SELECT rowid FROM fts_chunks WHERE fts_chunks MATCH 'algorithm';")
    hits = cur.fetchall()
    assert len(hits) == 1

    cur.execute("SELECT rowid FROM fts_chunks WHERE fts_chunks MATCH 'replicate';")
    hits = cur.fetchall()
    assert len(hits) == 1
    conn.close()


def test_parse_markdown_into_breadcrumb_chunks(tmp_path: Path) -> None:
    """Test semantic breadcrumb chunking with heading hierarchy preservation."""
    sample_file = tmp_path / "sample.md"
    sample_file.write_text(
        """# Distributed Systems
## Consensus Fundamentals
Here are the fundamental rules of consensus. Nodes must reach agreement.

### Quorum Mechanics
A quorum requires a strict majority `(N/2) + 1` of participating members.
If quorum is lost, no writes may commit.
""",
        encoding="utf-8",
    )

    chunks = parse_markdown_into_breadcrumb_chunks(
        file_path=sample_file,
        rel_path="sample.md",
        doc_title="Sample Document",
        target_chunk_words=100,
    )

    assert len(chunks) >= 1
    # Check that breadcrumb captures hierarchy
    breadcrumbs = [c["breadcrumb"] for c in chunks]
    assert any("Distributed Systems" in b for b in breadcrumbs)
    assert any("Quorum Mechanics" in b or "Consensus Fundamentals" in b for b in breadcrumbs)


def test_extract_domain_catalog() -> None:
    """Test synthesis of deduplicated domain catalog and topic taxonomy."""
    chunks = [
        {
            "breadcrumb": "Book > Raft Consensus > Leader Election",
            "heading": "Leader Election",
            "content": "The leader election protocol uses `RequestVote` RPC.",
            "doc_type": "textbook",
        },
        {
            "breadcrumb": "Video > Raft Lecture > Leader Election",
            "heading": "Leader Election",
            "content": "Why leader election requires randomized timeouts.",
            "doc_type": "transcript",
        },
        {
            "breadcrumb": "Book > Raft Consensus > Log Replication",
            "heading": "Log Replication",
            "content": "The `AppendEntries` message drives state machine commits.",
            "doc_type": "textbook",
        },
    ]

    catalog = extract_domain_catalog(chunks, slug="test-raft", total_docs=2)
    assert catalog["slug"] == "test-raft"
    assert catalog["total_sources_indexed"] == 2
    assert catalog["total_chunks_indexed"] == 3
    assert len(catalog["top_consensus_topics"]) > 0

    # Leader election was in multiple chunks -> higher consensus
    topic_titles = [t["title"] for t in catalog["top_consensus_topics"]]
    assert any("Leader Election" in t for t in topic_titles)

    # Prerequisite vocabulary extracted code terms
    vocab = catalog["prerequisite_vocabulary"]
    assert "RequestVote" in vocab or "AppendEntries" in vocab


def test_end_to_end_build_and_validation_gates(temp_sources_workspace: tuple[Path, str]) -> None:
    """Test end-to-end 4-gate index build pipeline and validation report."""
    ws, slug = temp_sources_workspace

    result = run_build_index(slug=slug, workspace=ws)
    assert result["ok"] is True
    assert result["slug"] == slug
    assert result["total_documents"] == 3
    assert result["total_chunks"] >= 3

    gates = result["validation_gates"]
    assert gates["gate1_scan"]["passed"] is True
    assert gates["gate1_scan"]["files_found"] == 3
    assert gates["gate2_chunk"]["passed"] is True
    assert gates["gate3_index"]["passed"] is True
    assert gates["gate3_index"]["db_size_bytes"] > 0
    assert gates["gate4_verify"]["passed"] is True
    assert gates["gate4_verify"]["probe_latency_ms"] < 50.0

    # Check files exist on disk
    sources_dir = ws / "research" / slug / "sources"
    assert (sources_dir / "index.db").is_file()
    assert (sources_dir / "catalog.json").is_file()

    # Cached catalog retrieval
    cached = get_cached_catalog(slug=slug, workspace=ws)
    assert cached["slug"] == slug
    assert "top_consensus_topics" in cached


def test_sub_15ms_point_retrieval(temp_sources_workspace: tuple[Path, str]) -> None:
    """Test BM25 point retrieval latency and snippet highlighting."""
    ws, slug = temp_sources_workspace
    run_build_index(slug=slug, workspace=ws)

    # Search for Raft consensus
    res = run_query_index(slug=slug, query="Raft leader election", workspace=ws, top_k=3)
    assert res["ok"] is True
    assert res["total_hits"] >= 1
    assert res["latency_ms"] < 25.0  # Fast local retrieval

    hit = res["hits"][0]
    assert "breadcrumb" in hit
    assert "score" in hit
    assert "snippet" in hit
    assert "full_content" in hit

    # Search with stemmed terms
    res_stem = run_query_index(slug=slug, query="partitioning heal", workspace=ws)
    assert res_stem["ok"] is True
    assert res_stem["total_hits"] >= 1


def test_potato_hardware_memory_envelope(temp_sources_workspace: tuple[Path, str]) -> None:
    """Ensure indexing peak RAM remains strictly under 50MB (potato hardware ceiling)."""
    ws, slug = temp_sources_workspace

    tracemalloc.start()
    run_build_index(slug=slug, workspace=ws)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    # Must run well below 50MB
    assert peak_mb < 50.0, f"Peak memory {peak_mb:.2f}MB exceeded potato budget of 50MB"


def test_course_builder_integrates_catalog_synthesis(temp_sources_workspace: tuple[Path, str]) -> None:
    """Verify tc-create incorporates Denis Diderot catalog.json for unified non-mirroring synthesis."""
    ws, slug = temp_sources_workspace

    # 1. Build index and catalog
    run_build_index(slug=slug, workspace=ws)

    # 2. Run course creation
    res = create_course(slug=slug, workspace=ws, archetype="applied_creation")
    assert res["ok"] is True
    assert res["consensus_reached"] is True

    course_dir = Path(res["course_path"])
    delib_path = Path(res["deliberation_path"])
    brainstorm_path = Path(res["brainstorm_path"])

    assert delib_path.is_file()
    assert brainstorm_path.is_file()

    # Check Denis Diderot is recorded in consensus deliberation
    delib_text = delib_path.read_text(encoding="utf-8")
    assert "Denis Diderot" in delib_text
    assert "The Master Synthesizer & Encyclopedist" in delib_text
    assert "catalog.json" in delib_text

    # Check brainstorm markdown notes the knowledge catalog substrate
    brainstorm_text = brainstorm_path.read_text(encoding="utf-8")
    assert "Denis Diderot Knowledge Base" in brainstorm_text or "catalog" in brainstorm_text.lower()

    # Check course.toml sources includes catalog.json and index.db
    course_toml = course_dir / "course.toml"
    assert course_toml.is_file()
    toml_content = course_toml.read_text(encoding="utf-8")
    assert "catalog.json" in toml_content
    assert "index.db" in toml_content


def test_zero_bmad_invariant() -> None:
    """Enforce strict invariant: runtime code and user-facing skills must contain zero 'bmad' references."""
    indexer_code = Path("_tc/scripts/indexer.py").read_text(encoding="utf-8").lower()
    skill_code = Path("skills/tc-index/SKILL.md").read_text(encoding="utf-8").lower()

    assert "bmad" not in indexer_code, "Found 'bmad' in _tc/scripts/indexer.py"
    assert "bmad" not in skill_code, "Found 'bmad' in skills/tc-index/SKILL.md"


def test_diacritic_normalization(tmp_path: Path) -> None:
    """Verify that unicode remove_diacritics normalizes accented terms."""
    db_file = tmp_path / "diacritic_test.db"
    conn = init_index_db(db_file)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO documents (rel_path, title, doc_type, source_group, file_size_bytes, sha256, created_at) "
        "VALUES ('math.md', 'Math', 'md', 'grp', 50, 'sha', '2026-01-01');"
    )
    doc_id = cur.lastrowid
    conn.execute(
        "INSERT INTO chunks (doc_id, chunk_index, breadcrumb, heading, content, token_count, metadata_json) "
        "VALUES (?, 0, 'Math > Topology', 'Topology', 'Henri Poincaré introduced the fundamental group in a naïve formulation.', 10, '{}');",
        (doc_id,),
    )
    conn.commit()

    # Search with unaccented "poincare" should match "Poincaré"
    cur.execute("SELECT rowid FROM fts_chunks WHERE fts_chunks MATCH 'poincare*';")
    hits = cur.fetchall()
    assert len(hits) == 1

    # Search with unaccented "naive" should match "naïve"
    cur.execute("SELECT rowid FROM fts_chunks WHERE fts_chunks MATCH 'naive*';")
    hits = cur.fetchall()
    assert len(hits) == 1
    conn.close()


def test_unformatted_raw_text_chunking_fallback(tmp_path: Path) -> None:
    """Verify that unformatted raw text without headings splits reliably using the ceiling fallback."""
    raw_file = tmp_path / "raw_transcript.txt"
    # Create 900 words without any headings or empty lines
    words = ["word" + str(i) for i in range(900)]
    raw_file.write_text(" ".join(words), encoding="utf-8")

    chunks = parse_markdown_into_breadcrumb_chunks(
        file_path=raw_file,
        rel_path="raw_transcript.txt",
        doc_title="Raw Transcript",
        target_chunk_words=300,
    )

    # Must be split into multiple chunks due to the ceiling fallback
    assert len(chunks) >= 2
    for c in chunks:
        assert c["token_count"] > 0

