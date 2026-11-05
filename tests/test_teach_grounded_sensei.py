"""tests/test_teach_grounded_sensei.py — Test suite for Grounded Sensei Runtime Grounding & Vocabulary Contract Gate (CAP-6)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from source_mapper import compile_source_map
from teach_engine import get_teaching_session, verify_vocabulary_turn

TEACH_SCRIPT = SCRIPTS_DIR / "teach_engine.py"


@pytest.fixture
def grounded_sensei_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace with multi-source course, source-map.toml, and lesson plans."""
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True)

    # 1. Raw sources
    raw_dir = ws / "research" / "distributed-storage" / "sources" / "raw"
    raw_dir.mkdir(parents=True)

    # Book A: DDIA
    (raw_dir / "ddia.md").write_text(
        """# Designing Data-Intensive Applications
## Chapter 3: Storage Engines
### LSM-Trees
Log-Structured Merge-Trees write to an in-memory memtable before flushing to SSTables.
""",
        encoding="utf-8",
    )

    # Book B: Database Internals
    (raw_dir / "db_internals.md").write_text(
        """# Database Internals
## Part II: LSM Storage Engines
LSM trees optimize write throughput with sequential disk access and background compaction.
""",
        encoding="utf-8",
    )

    # 2. Course directory
    course_dir = ws / "courses" / "distributed-storage"
    course_dir.mkdir(parents=True)

    course_data = {
        "course": {
            "id": "distributed-storage",
            "title": "Distributed Storage Engines",
            "archetype": "axiomatic_primitives",
        },
        "chapters": [
            {
                "id": "chapter-01",
                "title": "Storage Fundamentals",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "Foundational Storage Models",
                        "status": "completed",
                        "vocabulary_introduced": ["Append-Only Log", "Hash Index"],
                    },
                    {
                        "id": "sec-02",
                        "title": "LSM-Tree Storage Engines",
                        "status": "in_progress",
                        "vocabulary_introduced": ["LSM-Trees"],
                    },
                ],
            }
        ],
    }

    import tomli_w
    (course_dir / "course.toml").write_text(tomli_w.dumps(course_data), encoding="utf-8")

    # 3. Lesson plans
    sec2_dir = course_dir / "chapter-01" / "sec-02"
    sec2_dir.mkdir(parents=True)
    (sec2_dir / "lesson-plan.md").write_text(
        """# Lesson Plan: LSM-Tree Storage Engines
## Objectives
- [ ] Master mechanics of LSM-Trees.
- [ ] Understand memtable flush and compaction.
""",
        encoding="utf-8",
    )

    # Compile source-map.toml
    compile_source_map("distributed-storage", workspace=ws)

    return ws


def test_grounded_sensei_session_loads_source_map_and_contract(grounded_sensei_workspace: Path) -> None:
    """Verify get_teaching_session loads exact source slices and injects vocabulary contract."""
    ws = grounded_sensei_workspace
    sess = get_teaching_session("distributed-storage", workspace=ws)

    assert sess["ok"] is True
    assert sess["active_section"]["section_id"] == "sec-02"

    # Verify O(1) loaded source excerpts with dialectic flag
    excerpts = sess.get("rag_source_excerpts", [])
    assert len(excerpts) >= 1
    lsm_ex = next((e for e in excerpts if "lsm" in e.get("section_title", "").lower() or "lsm" in e.get("source_id", "").lower()), None)
    assert lsm_ex is not None
    assert lsm_ex["dialectic"] is True  # Sourced from multiple peer books!

    # Verify Vocabulary Contract
    contract = sess.get("vocabulary_contract")
    assert contract is not None
    assert contract["intuition_before_label"] is True
    assert "Append-Only Log" in contract["approved_terms"]
    assert "Hash Index" in contract["approved_terms"]
    assert contract["dialectic"] is True
    assert len(contract["rules"]) >= 2


def test_verify_vocabulary_turn_valid_plain_english() -> None:
    """Verify that an instructional turn introducing target term with intuition passes gate."""
    approved = ["Append-Only Log", "Hash Index"]
    target = "LSM-Trees"

    # Plain English explanation introducing target term
    good_turn = (
        "Imagine writing all your daily notes into a fast notepad on your desk. "
        "When the notepad fills up, you file it into a cabinet in alphabetical order. "
        "In storage systems, this structure is called **LSM-Trees**. We keep recent writes in memory."
    )

    res = verify_vocabulary_turn(turn_text=good_turn, approved_terms=approved, target_term=target)
    assert res["ok"] is True
    assert res["unearned_terms"] == []
    assert "lsm-trees" in res["approved_terms_used"]


def test_verify_vocabulary_turn_rejects_unearned_jargon() -> None:
    """Verify that using unearned technical primitives without antecedent fails the gate."""
    approved = ["Append-Only Log"]
    target = "LSM-Trees"

    # Turn inappropriately dumps unintroduced jargon: Merkle trees, Bw-Trees, Bloom filters
    bad_turn = (
        "We optimize the writes using **LSM-Trees**, but to speed up point queries we check a **Bloom filter** "
        "and synchronize epoch memory using a **Bw-Tree** lock-free architecture."
    )

    res = verify_vocabulary_turn(turn_text=bad_turn, approved_terms=approved, target_term=target)
    assert res["ok"] is False
    assert len(res["unearned_terms"]) >= 1
    assert any("bloom" in term for term in res["unearned_terms"])
    assert any("bw-tree" in term or "bw" in term for term in res["unearned_terms"])


def test_teach_engine_cli_verify_vocab(grounded_sensei_workspace: Path) -> None:
    """Verify teach_engine.py verify-vocab CLI subcommand output and exit codes."""
    ws = grounded_sensei_workspace

    # Valid turn
    res_pass = subprocess.run(
        [
            sys.executable,
            str(TEACH_SCRIPT),
            "verify-vocab",
            "--course",
            "distributed-storage",
            "--text",
            "We organize records in memory before flushing them. This is known as **LSM-Trees**.",
            "--workspace",
            str(ws),
        ],
        capture_output=True,
        text=True,
    )
    assert res_pass.returncode == 0
    pass_data = json.loads(res_pass.stdout)
    assert pass_data["ok"] is True

    # Invalid turn with unearned jargon
    res_fail = subprocess.run(
        [
            sys.executable,
            str(TEACH_SCRIPT),
            "verify-vocab",
            "--course",
            "distributed-storage",
            "--text",
            "We enforce safety with **Raft Consensus** and **Vector Clocks**.",
            "--workspace",
            str(ws),
        ],
        capture_output=True,
        text=True,
    )
    assert res_fail.returncode == 1
    fail_data = json.loads(res_fail.stdout or res_fail.stderr)
    assert fail_data["ok"] is False
    assert len(fail_data["unearned_terms"]) >= 1


def test_zero_bmad_invariant() -> None:
    """Verify teach_engine.py contains strictly zero mentions of bmad."""
    content = TEACH_SCRIPT.read_text(encoding="utf-8").lower()
    assert "bmad" not in content, f"Found 'bmad' in {TEACH_SCRIPT}"
