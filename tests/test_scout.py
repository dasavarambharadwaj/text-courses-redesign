"""tests/test_scout.py — Comprehensive test suite for documentation scout and research caching engine."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCOUT_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "scout.py"
SKILL_FILE = Path(__file__).parent.parent / "skills" / "tc-research" / "SKILL.md"


def test_scout_cli_help():
    """Verify scout CLI prints help message and exits 0."""
    res = subprocess.run([sys.executable, str(SCOUT_SCRIPT), "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "scout" in res.stdout
    assert "get" in res.stdout
    assert "list" in res.stdout


def test_scout_pep_723_metadata():
    """Verify script contains valid PEP 723 metadata header."""
    content = SCOUT_SCRIPT.read_text(encoding="utf-8")
    assert "# /// script" in content
    assert 'requires-python = ">=3.11"' in content
    assert "tomli-w>=" in content
    assert "# ///" in content


def test_zero_bmad_references():
    """Verify strict zero-BMad references in scripts and skill documentation."""
    for target in [SCOUT_SCRIPT, SKILL_FILE]:
        text = target.read_text(encoding="utf-8")
        assert not re.search(r"\bbmad\b", text, re.IGNORECASE), f"Found BMad mention in {target}"


def test_scout_local_file_extraction(tmp_path: Path):
    """Verify scout extracts ToC, API symbols, and vocabulary from a local documentation file."""
    doc_file = tmp_path / "sqlite_engine.md"
    doc_file.write_text(
        "# SQLite Storage Engine\n\n"
        "## B-Tree Architecture\n"
        "The **b-tree** structure provides balanced search.\n\n"
        "```python\ndef pager_read_page(pgno: int) -> bytes:\n    pass\n\n"
        "class BTreeNode:\n    pass\n```\n\n"
        "### Wal Protocol\n"
        "Write-ahead logging uses `wal_index` and `shm` files.\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            str(SCOUT_SCRIPT),
            "scout",
            "--slug",
            "sqlite-internals",
            "--workspace",
            str(tmp_path),
            "--source-path",
            str(doc_file),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["slug"] == "sqlite-internals"
    assert data["confidence"] == "high"

    digest_file = tmp_path / ".tc" / "research" / "sqlite-internals" / "digest.json"
    sources_file = tmp_path / ".tc" / "research" / "sqlite-internals" / "sources.toml"
    assert digest_file.is_file()
    assert sources_file.is_file()

    digest = json.loads(digest_file.read_text(encoding="utf-8"))
    assert digest["confidence"] == "high"
    assert len(digest["toc"]) >= 3
    headings = [h["title"] for h in digest["toc"]]
    assert "SQLite Storage Engine" in headings
    assert "B-Tree Architecture" in headings

    api_names = [a["name"] for a in digest["api_index"]]
    assert "pager_read_page" in api_names
    assert "BTreeNode" in api_names

    vocab = digest["vocabulary"]
    assert "b-tree" in vocab or "wal_index" in vocab


def test_scout_topic_fallback_confidence(tmp_path: Path):
    """Verify scout on pure topic description assigns medium confidence fallback."""
    res = subprocess.run(
        [
            sys.executable,
            str(SCOUT_SCRIPT),
            "scout",
            "--slug",
            "raft-consensus",
            "--workspace",
            str(tmp_path),
            "--topic",
            "Distributed Raft Consensus Algorithm",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["confidence"] == "medium"


def test_scout_confidence_override_and_validation(tmp_path: Path):
    """Verify explicit confidence override works and invalid values are rejected."""
    # Valid override
    res_valid = subprocess.run(
        [
            sys.executable,
            str(SCOUT_SCRIPT),
            "scout",
            "--slug",
            "custom-topic",
            "--workspace",
            str(tmp_path),
            "--topic",
            "Custom Notes",
            "--confidence",
            "low",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_valid.returncode == 0
    data = json.loads(res_valid.stdout)
    assert data["confidence"] == "low"

    # Invalid override
    res_invalid = subprocess.run(
        [
            sys.executable,
            str(SCOUT_SCRIPT),
            "scout",
            "--slug",
            "custom-topic",
            "--workspace",
            str(tmp_path),
            "--topic",
            "Custom Notes",
            "--confidence",
            "ultra-high",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_invalid.returncode == 1
    err_data = json.loads(res_invalid.stderr)
    assert "Invalid confidence" in err_data["error"]


def test_get_cached_digest_and_list(tmp_path: Path):
    """Verify get retrieves cached research digest and list enumerates topics."""
    # Pre-scout a topic
    subprocess.run(
        [
            sys.executable,
            str(SCOUT_SCRIPT),
            "scout",
            "--slug",
            "compiler-basics",
            "--workspace",
            str(tmp_path),
            "--topic",
            "AST and Lexer Foundations",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # 1. Test get
    res_get = subprocess.run(
        [
            sys.executable,
            str(SCOUT_SCRIPT),
            "get",
            "--slug",
            "compiler-basics",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_get.returncode == 0
    digest = json.loads(res_get.stdout)
    assert digest["slug"] == "compiler-basics"
    assert "toc" in digest

    # 2. Test get nonexistent slug fails
    res_missing = subprocess.run(
        [
            sys.executable,
            str(SCOUT_SCRIPT),
            "get",
            "--slug",
            "nonexistent-topic",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_missing.returncode == 1

    # 3. Test list
    res_list = subprocess.run(
        [
            sys.executable,
            str(SCOUT_SCRIPT),
            "list",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_list.returncode == 0
    list_data = json.loads(res_list.stdout)
    assert len(list_data["research_topics"]) == 1
    assert list_data["research_topics"][0]["slug"] == "compiler-basics"
