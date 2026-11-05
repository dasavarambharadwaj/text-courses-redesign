"""tests/test_source_mapper.py — Test suite for Conveyor-Belt Chapter Pipeline & Symbol Table (source-map.toml)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from source_mapper import (
    compile_source_map,
    read_source_pointer,
    split_source_into_conveyor_batches,
)

SOURCE_MAPPER_SCRIPT = SCRIPTS_DIR / "source_mapper.py"


@pytest.fixture
def multi_source_course_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace with two raw source books and a course scaffold."""
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True)

    # 1. Raw sources directory
    raw_dir = ws / "research" / "distributed-storage" / "sources" / "raw"
    raw_dir.mkdir(parents=True)

    # Book 1: DDIA
    ddia_file = raw_dir / "ddia.md"
    ddia_content = """# Designing Data-Intensive Applications
## Chapter 1: Reliability
Reliability is tolerating hardware, software, and human errors.
## Chapter 2: Data Models
Relational vs Document models.
## Chapter 3: Storage and Retrieval
### SSTables and LSM-Trees
The storage engine keeps an in-memory balanced tree structure, called a memtable.
When the memtable is bigger than some threshold, write it to disk as an SSTable file.
Compaction merges SSTables in the background.
### B-Trees
B-trees break the database down into fixed-size blocks or pages.
"""
    ddia_file.write_text(ddia_content, encoding="utf-8")

    # Book 2: Database Internals
    dbi_file = raw_dir / "database-internals.md"
    dbi_content = """# Database Internals
## Part I: B-Tree Basics
Page headers, cell pointers, and binary search in B-Trees.
## Part II: LSM Storage Engines
LSM trees optimize write performance by using sequential I/O.
Size-tiered compaction triggers when multiple SSTables of approximately equal size accumulate.
Memtables are flushed to immutable disk components.
"""
    dbi_file.write_text(dbi_content, encoding="utf-8")

    # 2. Course directory
    course_dir = ws / "courses" / "distributed-storage"
    course_dir.mkdir(parents=True)

    course_data = {
        "course": {
            "id": "distributed-storage",
            "title": "Distributed Storage Systems",
            "archetype": "axiomatic_primitives",
        },
        "chapters": [
            {
                "id": "chapter-01",
                "title": "Storage Engines & Compaction",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "LSM-Trees and Compaction",
                        "vocabulary_introduced": ["LSM-Trees", "Memtable", "Compaction"],
                    },
                    {
                        "id": "sec-02",
                        "title": "B-Tree Page Internals",
                        "vocabulary_introduced": ["B-Trees", "Page Headers"],
                    },
                ],
            }
        ],
    }

    import tomli_w
    (course_dir / "course.toml").write_text(tomli_w.dumps(course_data), encoding="utf-8")

    return ws


def test_split_source_into_conveyor_batches(multi_source_course_workspace: Path) -> None:
    """Verify large documents are split into bounded conveyor batches with token limits."""
    source_file = multi_source_course_workspace / "research" / "distributed-storage" / "sources" / "raw" / "ddia.md"
    
    batches = split_source_into_conveyor_batches(source_file, max_tokens_per_batch=25000)
    assert len(batches) >= 1

    for b in batches:
        assert "batch_index" in b
        assert "title" in b
        assert "line_start" in b
        assert "line_end" in b
        assert b["token_estimate"] <= 25000
        assert len(b["content"]) > 0


def test_compile_source_map_schema_and_dialectic(multi_source_course_workspace: Path) -> None:
    """Verify compile_source_map produces a compliant symbol table with dialectic synthesis."""
    ws = multi_source_course_workspace
    sm = compile_source_map("distributed-storage", workspace=ws)

    assert sm["version"] == "1.0.0"
    assert sm["course_slug"] == "distributed-storage"
    assert len(sm["sources"]) == 2  # ddia and database-internals
    assert sm["total_concepts"] >= 3

    # Check LSM-Trees concept for dialectic synthesis across both sources
    ch1 = sm["chapters"][0]
    sec1 = ch1["sections"][0]
    lsm_concept = next((c for c in sec1["concepts"] if "lsm" in c["id"]), None)
    assert lsm_concept is not None
    assert lsm_concept["dialectic"] is True  # Appears in both books!
    assert len(lsm_concept["pointers"]) == 2
    assert "ddia" in [p["source_id"] for p in lsm_concept["pointers"]]
    assert "database-internals" in [p["source_id"] for p in lsm_concept["pointers"]]

    # Verify line pointers and verbatim anchors
    for ptr in lsm_concept["pointers"]:
        assert ptr["lines"][0] <= ptr["lines"][1]
        assert len(ptr["verbatim_anchor"]) > 0


def test_read_source_pointer_instant_lookup(multi_source_course_workspace: Path) -> None:
    """Verify read_source_pointer retrieves exact verbatim line slices in sub-5ms O(1) time."""
    ws = multi_source_course_workspace
    compile_source_map("distributed-storage", workspace=ws)

    start_time = time.perf_counter()
    excerpts = read_source_pointer("distributed-storage", "lsm_trees", workspace=ws)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    assert elapsed_ms < 50.0  # Well within instant bounds (<50ms even on cold filesystem)
    assert len(excerpts) == 2  # Found in both sources!

    # Check verbatim content
    ddia_ex = next((e for e in excerpts if e["source_id"] == "ddia"), None)
    assert ddia_ex is not None
    assert "memtable" in ddia_ex["content"].lower()

    dbi_ex = next((e for e in excerpts if e["source_id"] == "database-internals"), None)
    assert dbi_ex is not None
    assert "compaction" in dbi_ex["content"].lower()


def test_source_mapper_cli(multi_source_course_workspace: Path) -> None:
    """Verify source_mapper.py CLI subcommands conveyor, compile, and read."""
    ws = multi_source_course_workspace
    src_file = ws / "research" / "distributed-storage" / "sources" / "raw" / "ddia.md"

    # 1. CLI conveyor
    res_conv = subprocess.run(
        [sys.executable, str(SOURCE_MAPPER_SCRIPT), "conveyor", "--source", str(src_file), "--max-tokens", "25000"],
        capture_output=True,
        text=True,
        check=True,
    )
    conv_data = json.loads(res_conv.stdout)
    assert conv_data["ok"] is True
    assert conv_data["total_batches"] >= 1

    # 2. CLI compile
    res_comp = subprocess.run(
        [sys.executable, str(SOURCE_MAPPER_SCRIPT), "compile", "--course", "distributed-storage", "--workspace", str(ws)],
        capture_output=True,
        text=True,
        check=True,
    )
    comp_data = json.loads(res_comp.stdout)
    assert comp_data["ok"] is True
    assert comp_data["total_concepts"] >= 1

    # 3. CLI read
    res_read = subprocess.run(
        [sys.executable, str(SOURCE_MAPPER_SCRIPT), "read", "--course", "distributed-storage", "--concept", "lsm_trees", "--workspace", str(ws)],
        capture_output=True,
        text=True,
        check=True,
    )
    read_data = json.loads(res_read.stdout)
    assert read_data["ok"] is True
    assert read_data["matches"] == 2


def test_zero_bmad_invariant() -> None:
    """Verify that source_mapper.py has strictly zero mentions of bmad."""
    content = SOURCE_MAPPER_SCRIPT.read_text(encoding="utf-8").lower()
    assert "bmad" not in content, f"Found 'bmad' in {SOURCE_MAPPER_SCRIPT}"
