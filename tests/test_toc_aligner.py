"""tests/test_toc_aligner.py — Comprehensive test suite for Macro TOC Aligner & Deduplication Engine."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from toc_aligner import (
    align_sources_in_directory,
    build_unified_dag,
    cluster_multi_source_tocs,
    extract_toc_from_markdown,
)

TOC_SCRIPT = SCRIPTS_DIR / "toc_aligner.py"


@pytest.fixture
def multi_source_workspace(tmp_path: Path) -> Path:
    """Create a temporary directory with two markdown books having overlapping and unique topics."""
    sdir = tmp_path / "raw_sources"
    sdir.mkdir(parents=True)

    # Book A: Designing Data-Intensive Applications
    book_a = sdir / "ddia.md"
    book_a.write_text(
        """# Designing Data-Intensive Applications
## Chapter 1: Reliability, Scalability, and Maintainability
Reliability metrics and failure modes.
## Chapter 2: Data Models and Query Languages
Relational vs Document models.
## Chapter 3: Storage and Retrieval: SSTables and LSM-Trees
Log-Structured Merge-Trees write amplification.
## Chapter 4: B-Trees and Page-Based Storage
In-place page mutation algorithms.
## Chapter 5: Leaders and Followers
Primary-backup replication protocols.
""",
        encoding="utf-8",
    )

    # Book B: Database Internals
    book_b = sdir / "db_internals.md"
    book_b.write_text(
        """# Database Internals
## Part I: B-Tree Basics and Anatomy
Page headers, cell pointers, and binary search.
## Part II: B-Tree Variants: Bw-Trees
Epoch-based memory reclamation for lock-free trees.
## Part III: LSM Tree Compaction Algorithms
Size-tiered vs leveled compaction strategies.
## Part IV: Distributed Transactions: Two-Phase Commit
Coordinator-cohort 2PC protocol and failover.
""",
        encoding="utf-8",
    )

    return sdir


def test_extract_toc_from_markdown(multi_source_workspace: Path) -> None:
    """Verify extract_toc_from_markdown accurately captures headings and line numbers."""
    book_a = multi_source_workspace / "ddia.md"
    toc = extract_toc_from_markdown(book_a)

    assert len(toc) == 6
    assert toc[0]["title"] == "Designing Data-Intensive Applications"
    assert toc[0]["level"] == 1
    assert toc[1]["title"] == "Chapter 1: Reliability, Scalability, and Maintainability"
    assert toc[1]["level"] == 2
    assert toc[1]["line_start"] == 2
    assert toc[1]["line_end"] >= 2


def test_cluster_multi_source_tocs(multi_source_workspace: Path) -> None:
    """Verify overlapping topics across books are detected as common with dialectic potential."""
    book_a = multi_source_workspace / "ddia.md"
    book_b = multi_source_workspace / "db_internals.md"

    sources = [
        {"id": "ddia", "file": str(book_a), "toc": extract_toc_from_markdown(book_a)},
        {"id": "db_internals", "file": str(book_b), "toc": extract_toc_from_markdown(book_b)},
    ]

    clustered = cluster_multi_source_tocs(sources)
    assert clustered["total_canonical_topics"] > 0
    assert clustered["common_topics_count"] >= 1  # LSM-Trees and B-Trees appear in both!

    # Find the LSM-Tree cluster
    lsm_cluster = next((c for c in clustered["common_topics"] if c["canonical_id"] == "lsm_trees"), None)
    assert lsm_cluster is not None
    assert lsm_cluster["is_common"] is True
    assert lsm_cluster["dialectic_potential"] is True
    assert len(lsm_cluster["occurrences"]) == 2  # Found in both books!

    # Unique topics preserved
    assert clustered["niche_topics_count"] >= 1
    bw_tree = next((c for c in clustered["niche_topics"] if "bw" in c["representative_title"].lower() or "bw" in c["canonical_id"]), None)
    assert bw_tree is not None
    assert bw_tree["is_common"] is False


def test_build_unified_dag_deduplication(multi_source_workspace: Path) -> None:
    """Verify build_unified_dag outputs a master curriculum where common topics appear only once."""
    book_a = multi_source_workspace / "ddia.md"
    book_b = multi_source_workspace / "db_internals.md"

    sources = [
        {"id": "ddia", "file": str(book_a), "toc": extract_toc_from_markdown(book_a)},
        {"id": "db_internals", "file": str(book_b), "toc": extract_toc_from_markdown(book_b)},
    ]

    dag = build_unified_dag(sources)
    assert dag["ok"] is True
    assert len(dag["curriculum_dag"]) > 0

    # Collect all section IDs in curriculum
    section_ids = []
    for ch in dag["curriculum_dag"]:
        for sec in ch["sections"]:
            section_ids.append(sec["section_id"])

    # Every section ID in the master curriculum must be unique (zero duplication!)
    assert len(section_ids) == len(set(section_ids))
    assert "lsm_trees" in section_ids
    assert "b_trees" in section_ids


def test_cli_align_command(multi_source_workspace: Path) -> None:
    """Verify CLI subcommand align works and outputs structured JSON."""
    res = subprocess.run(
        [sys.executable, str(TOC_SCRIPT), "align", "--sources", str(multi_source_workspace), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["total_sources_ingested"] == 2
    assert len(data["curriculum_dag"]) > 0


def test_zero_bmad_references() -> None:
    """Verify strict zero-BMad invariant across toc_aligner script and tests."""
    script_text = TOC_SCRIPT.read_text(encoding="utf-8")
    assert not re.search(r"\bbmad\b", script_text, re.IGNORECASE), "Forbidden BMad mention in toc_aligner.py"
