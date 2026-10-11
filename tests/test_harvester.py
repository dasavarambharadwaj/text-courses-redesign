"""tests/test_harvester.py — Comprehensive unit tests for Multi-Source Deep Harvester (FR-43).

Verifies:
1. GitHub repo URL normalization across full URLs, shorthand, and .git paths.
2. WebVTT subtitle cleaning and rolling caption deduplication.
3. Gold-standard consensus recording and acquisition badges.
4. Multi-source directory scanning and indexing (sources-index.json).
5. Integration with scout.py (enriching dossiers with gold standards and harvested assets).
6. Dispatcher routing via tc.py harvest.
7. Strict zero-BMad references invariant across all harvester code and skills.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

HARVESTER_SCRIPT = SCRIPTS_DIR / "harvester.py"
SCOUT_SCRIPT = SCRIPTS_DIR / "scout.py"
TC_SCRIPT = SCRIPTS_DIR / "tc.py"
SKILL_RESEARCH = PROJECT_ROOT / "skills" / "tc-research" / "SKILL.md"


def test_zero_bmad_references_in_harvester():
    """Verify strict zero-BMad references in harvester script and tc-research skill."""
    for path in [HARVESTER_SCRIPT, SCOUT_SCRIPT, SKILL_RESEARCH]:
        content = path.read_text(encoding="utf-8")
        assert not re.search(r"\bbmad\b", content, re.IGNORECASE), f"BMad mention found in {path}"


def test_harvester_pep_723_metadata():
    """Verify harvester script contains valid PEP 723 metadata."""
    content = HARVESTER_SCRIPT.read_text(encoding="utf-8")
    assert "# /// script" in content
    assert 'requires-python = ">=3.11"' in content
    assert "# ///" in content


def test_harvester_cli_help():
    """Verify harvester CLI displays help and lists core subcommands."""
    res = subprocess.run([sys.executable, str(HARVESTER_SCRIPT), "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "harvest-repo" in res.stdout
    assert "harvest-youtube" in res.stdout
    assert "record-consensus" in res.stdout
    assert "ingest-sources" in res.stdout


def test_normalize_github_url():
    """Verify github identifier normalization."""
    from harvester import normalize_github_url

    clone_url, owner, repo = normalize_github_url("https://github.com/rust-lang/book")
    assert clone_url == "https://github.com/rust-lang/book.git"
    assert owner == "rust-lang"
    assert repo == "book"

    clone_url, owner, repo = normalize_github_url("rust-lang/book.git")
    assert owner == "rust-lang"
    assert repo == "book"

    clone_url, owner, repo = normalize_github_url("mit-pdos/xv6-riscv")
    assert owner == "mit-pdos"
    assert repo == "xv6-riscv"
    assert clone_url == "https://github.com/mit-pdos/xv6-riscv.git"


def test_clean_vtt_subtitles():
    """Verify VTT subtitle cleaning and caption deduplication."""
    from harvester import clean_vtt_subtitles

    raw_vtt = """WEBVTT
Kind: captions
Language: en

00:00:01.000 --> 00:00:04.000 align:start position:0%
Welcome to the
Welcome to the lecture on Rust lifetimes.

00:00:04.050 --> 00:00:07.000 align:start position:0%
Today we will cover
Today we will cover borrowing and reference safety.
"""

    cleaned = clean_vtt_subtitles(raw_vtt)
    assert "Welcome to the lecture on Rust lifetimes." in cleaned
    assert "borrowing and reference safety." in cleaned
    # Ensure duplicate rolling text is removed
    assert cleaned.count("Welcome to the") == 1
    assert cleaned.count("Today we will cover") == 1


def test_record_gold_standards(tmp_path: Path):
    """Verify gold-standard consensus recording with appropriate status badges."""
    from harvester import record_gold_standards

    slug = "distributed-consensus"
    topic = "Distributed Systems Consensus"
    summary = "Community consensus across Hacker News and Reddit highlights Paxos, Raft, and Designing Data-Intensive Applications."
    items = [
        {
            "title": "Designing Data-Intensive Applications",
            "author": "Martin Kleppmann",
            "type": "commercial_book",
            "status": "USER_PROVIDED_NEEDED",
            "location": "sources/ddia.pdf",
        },
        {
            "title": "In Search of an Understandable Consensus Algorithm (Raft)",
            "author": "Ongaro & Ousterhout",
            "type": "paper",
            "status": "HARVESTED",
            "location": "sources/repos/raft-paper/raft.md",
        },
        {
            "title": "MIT 6.824: Distributed Systems Lecture 6",
            "author": "Robert Morris",
            "type": "video_lecture",
            "status": "TRANSCRIPT_EXTRACTED",
            "location": "sources/transcripts/mit-6824-lecture6.md",
        },
    ]

    res = record_gold_standards(
        slug=slug,
        topic=topic,
        consensus_summary=summary,
        gold_standard_items=items,
        workspace=tmp_path,
    )
    assert res["ok"] is True
    assert res["total_items"] == 3

    gold_file = tmp_path / "research" / slug / "gold-standards.md"
    assert gold_file.is_file()
    content = gold_file.read_text(encoding="utf-8")
    assert "Community Consensus & Gold-Standard Materials" in content
    assert "Designing Data-Intensive Applications" in content
    assert "[ACQUISITION NEEDED" in content
    assert "[HARVESTED" in content
    assert "[TRANSCRIPT EXTRACTED]" in content
    assert "research/distributed-consensus/sources/" in content


def test_ingest_sources_directory(tmp_path: Path):
    """Verify scanning and indexing of research/<slug>/sources/ directory."""
    from harvester import ingest_sources_directory

    slug = "db-internals"
    sources_dir = tmp_path / "research" / slug / "sources"
    transcripts_dir = sources_dir / "transcripts"
    repos_dir = sources_dir / "repos" / "sqlite-doc"

    transcripts_dir.mkdir(parents=True, exist_ok=True)
    repos_dir.mkdir(parents=True, exist_ok=True)

    # Add a transcript
    (transcripts_dir / "cmu-15445-lec01.md").write_text(
        "# Lecture 01: Relational Model\n\nDiscussion of relation algebra and tuples.\n",
        encoding="utf-8",
    )

    # Add a repo markdown file
    (repos_dir / "architecture.md").write_text(
        "# SQLite Architecture\n\nVirtual Machine, B-Tree, Pager, and OS Interface.\n",
        encoding="utf-8",
    )

    # Add a simulated user-provided PDF book
    (sources_dir / "database-system-concepts.pdf").write_bytes(b"%PDF-1.5 fake pdf content")

    res = ingest_sources_directory(slug=slug, workspace=tmp_path)
    assert res["ok"] is True
    assert res["total_sources"] == 3

    index_file = sources_dir / "sources-index.json"
    assert index_file.is_file()
    index_data = json.loads(index_file.read_text(encoding="utf-8"))
    assert index_data["total_sources"] == 3

    types = {s["type"] for s in index_data["sources"]}
    assert "youtube_transcript" in types
    assert "github_repo_content" in types
    assert "binary_book" in types


def test_harvest_github_repo_local_git(tmp_path: Path):
    """Verify harvest_github_repo shallow clones and indexes a local git repository."""
    from harvester import harvest_github_repo

    # Set up a dummy origin git repo
    origin_repo = tmp_path / "fake-textbook-origin"
    origin_repo.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(origin_repo)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(origin_repo), "config", "user.name", "Author"], check=True)
    subprocess.run(["git", "-C", str(origin_repo), "config", "user.email", "author@example.com"], check=True)

    (origin_repo / "chapter-01.md").write_text(
        "# Chapter 1: Introduction\n\nFoundations of computing systems.\n",
        encoding="utf-8",
    )
    (origin_repo / "chapter-02.md").write_text(
        "# Chapter 2: Memory Hierarchy\n\nCache lines, virtual memory, and TLBs.\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "-C", str(origin_repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(origin_repo), "commit", "-m", "Initial commit"], check=True)

    # Harvest into workspace
    slug = "sys-arch"
    res = harvest_github_repo(
        repo_identifier=str(origin_repo),
        slug=slug,
        workspace=tmp_path,
        branch="main",
    )
    assert res["ok"] is True
    assert res["files_count"] == 2
    assert "Chapter 1: Introduction" in res["toc_sample"]
    assert "Chapter 2: Memory Hierarchy" in res["toc_sample"]

    manifest_file = tmp_path / "research" / slug / "sources" / "repos" / origin_repo.name / "harvest-manifest.json"
    assert manifest_file.is_file()


def test_scout_integration_with_harvested_assets(tmp_path: Path):
    """Verify scout.py seamlessly ingests gold standards and harvested assets into dossier.md and sources.json."""
    from harvester import record_gold_standards
    from scout import run_scout

    slug = "compiler-design"
    # Pre-populate gold standards
    record_gold_standards(
        slug=slug,
        topic="Modern Compiler Design",
        consensus_summary="Dragon book and Modern Compiler Implementation in ML.",
        gold_standard_items=[
            {
                "title": "Compilers: Principles, Techniques, and Tools",
                "author": "Aho, Lam, Sethi, Ullman",
                "type": "commercial_book",
                "status": "acquisition_needed",
                "location": "sources/dragon-book.pdf",
            }
        ],
        workspace=tmp_path,
    )

    # Add a harvested transcript
    transcripts_dir = tmp_path / "research" / slug / "sources" / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    (transcripts_dir / "stanford-cs143-lexing.md").write_text(
        "# CS143: Lexical Analysis\n\nRegular expressions and DFAs.\n",
        encoding="utf-8",
    )

    # Run scout
    scout_res = run_scout(
        slug=slug,
        workspace=tmp_path,
        topic="Modern Compiler Design",
    )
    assert scout_res["ok"] is True
    assert scout_res["harvested_sources_count"] >= 1
    assert scout_res["confidence"] == "high"

    dossier_content = Path(scout_res["dossier_file"]).read_text(encoding="utf-8")
    assert "## 7. Gold-Standard Literature & Multi-Source Harvested Assets" in dossier_content
    assert "Compilers: Principles, Techniques, and Tools" in dossier_content

    sources_json_file = tmp_path / "research" / slug / "sources.json"
    assert sources_json_file.is_file()
    sources_data = json.loads(sources_json_file.read_text(encoding="utf-8"))
    assert len(sources_data["sources"]) >= 2
    harvested_types = [s["type"] for s in sources_data["sources"]]
    assert "youtube_transcript" in harvested_types


def test_tc_dispatcher_harvest_forwarding():
    """Verify tc.py routes directly to harvester subcommands."""
    res = subprocess.run(
        [sys.executable, str(TC_SCRIPT), "harvest", "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "harvest-repo" in res.stdout
    assert "harvest-youtube" in res.stdout
