"""tests/test_paper_and_book_scout.py — Tests for paper_fetcher.py and book_scout.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from book_scout import discover_canonical_books
from paper_fetcher import harvest_official_sources, match_canonical_specs, match_systems_docs


def test_match_canonical_specs():
    """Verify keyword matching accurately identifies canonical RFCs."""
    topic = "TLS 1.3 security, HTTP/2 multiplexing, and OAuth 2.0 authorization with JWT"
    specs = match_canonical_specs(topic)
    identifiers = {s["identifier"] for s in specs}
    assert "8446" in identifiers  # TLS 1.3
    assert "9113" in identifiers  # HTTP/2
    assert "6749" in identifiers  # OAuth 2.0
    assert "7519" in identifiers  # JWT


def test_match_systems_docs():
    """Verify systems keywords accurately match kernel manual pages."""
    topic = "Linux epoll event loop, syscalls, and virtual memory paging"
    docs = match_systems_docs(topic)
    names = {d["name"] for d in docs}
    assert "epoll_7" in names
    assert "virtual_memory_internals" in names
    assert "syscalls_and_context_switch" in names


def test_harvest_official_sources_creates_files(tmp_path: Path):
    """Verify harvest_official_sources writes real files to research/<slug>/sources/."""
    topic = "Linux epoll I/O event notification facility and virtual memory"
    slug = "test-systems"
    res = harvest_official_sources(slug=slug, topic=topic, workspace=tmp_path)
    assert res["ok"] is True
    assert res["total_harvested"] >= 2

    docs_dir = tmp_path / "research" / slug / "sources" / "docs"
    assert docs_dir.is_dir()
    assert (docs_dir / "epoll_7.md").is_file()
    assert (docs_dir / "virtual_memory_internals.md").is_file()


def test_discover_canonical_books_matches_domain():
    """Verify discover_canonical_books identifies landmark textbooks with authors and ISBNs."""
    topic = "Operating Systems, Linux Kernel, and TCP/IP Networking"
    slug = "os-net"
    res = discover_canonical_books(topic=topic, slug=slug, query_online=False)
    assert res["ok"] is True
    assert res["total_books"] >= 3

    titles = [b["title"] for b in res["books"]]
    assert any("Modern Operating Systems" in t for t in titles)
    assert any("Operating Systems: Three Easy Pieces" in t for t in titles)
    assert any("TCP/IP Illustrated" in t for t in titles)

    tanenbaum = next(b for b in res["books"] if "Modern Operating Systems" in b["title"])
    assert "Andrew S. Tanenbaum" in tanenbaum["authors"]
    assert tanenbaum["status"] == "acquisition_needed"

    ostep = next(b for b in res["books"] if "Three Easy Pieces" in b["title"])
    assert ostep["status"] == "auto_harvestable"


def test_zero_bmad_references_in_new_modules():
    """Verify new modules contain zero references to bmad."""
    paper_fetcher_code = (SCRIPTS_DIR / "paper_fetcher.py").read_text(encoding="utf-8").lower()
    book_scout_code = (SCRIPTS_DIR / "book_scout.py").read_text(encoding="utf-8").lower()
    assert "bmad" not in paper_fetcher_code
    assert "bmad" not in book_scout_code
