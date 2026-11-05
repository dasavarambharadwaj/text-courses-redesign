"""tests/test_auto_ingestion.py — Verification suite for drop-in workspace auto-ingestion (CAP-3)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from extractor import (
    auto_ingest_workspace,
    discover_workspace_documents,
)


def create_searchable_pdf(path: Path) -> Path:
    """Write minimal valid PDF with extractable text."""
    raw_pdf = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 135 >>
stream
BT
/F1 12 Tf
72 712 Td
(Chapter 1: Distributed Consensus and Leader Election) Tj
0 -24 Td
(def election_safety(): return True) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000430 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
510
%%EOF"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw_pdf)
    return path


def create_scanned_pdf(path: Path) -> Path:
    """Write minimal valid PDF with 0 extractable characters."""
    raw_pdf = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << >> >>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
190
%%EOF"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw_pdf)
    return path


def test_discover_workspace_documents_finds_pdfs_in_multiple_folders(tmp_path: Path):
    """Verify discovery finds PDFs in root, books, sources, research, and docs while excluding internal dirs."""
    root_pdf = create_searchable_pdf(tmp_path / "root-book.pdf")
    books_pdf = create_searchable_pdf(tmp_path / "books" / "ddia.pdf")
    sources_pdf = create_searchable_pdf(tmp_path / "sources" / "db-internals.pdf")
    research_pdf = create_searchable_pdf(tmp_path / "research" / "raft-paper.pdf")

    # Excluded directories
    create_searchable_pdf(tmp_path / ".tc" / "hidden.pdf")
    create_searchable_pdf(tmp_path / "_tc" / "internal.pdf")
    create_searchable_pdf(tmp_path / "tests" / "test.pdf")
    create_searchable_pdf(tmp_path / "sources" / "extracted" / "already.pdf")

    discovered = discover_workspace_documents(tmp_path)
    discovered_stems = {p.stem for p in discovered}

    assert "root-book" in discovered_stems
    assert "ddia" in discovered_stems
    assert "db-internals" in discovered_stems
    assert "raft-paper" in discovered_stems
    assert "hidden" not in discovered_stems
    assert "internal" not in discovered_stems
    assert "test" not in discovered_stems
    assert "already" not in discovered_stems


def test_auto_ingest_workspace_extracts_cleanly(tmp_path: Path):
    """Verify auto_ingest_workspace extracts digital PDFs to target directory."""
    book_pdf = create_searchable_pdf(tmp_path / "books" / "distributed-systems.pdf")

    res = auto_ingest_workspace(tmp_path)

    assert res["ok"] is True
    assert res["total_discovered"] == 1
    assert res["total_extracted"] == 1
    assert res["total_scanned"] == 0
    assert res["has_scanned_warnings"] is False

    extracted_file = tmp_path / "sources" / "extracted" / "distributed-systems.md"
    assert extracted_file.is_file()
    content = extracted_file.read_text(encoding="utf-8")
    assert "Distributed Consensus and Leader Election" in content


def test_auto_ingest_workspace_detects_scanned_pdf_and_gives_guidance(tmp_path: Path):
    """Verify pre-flight density probe detects scanned image PDF and generates empathetic guidance."""
    scanned_pdf = create_scanned_pdf(tmp_path / "books" / "scanned-notes.pdf")

    res = auto_ingest_workspace(tmp_path)

    assert res["total_discovered"] == 1
    assert res["total_extracted"] == 0
    assert res["total_scanned"] == 1
    assert res["has_scanned_warnings"] is True

    scanned_item = res["scanned"][0]
    assert scanned_item["filename"] == "scanned-notes.pdf"
    assert "scanned bitmap image without a digital text layer" in scanned_item["guidance"]
    assert "Please provide a digital text PDF, EPUB, or Markdown file" in scanned_item["guidance"]


def test_auto_ingest_cli(tmp_path: Path):
    """Verify extractor.py auto-ingest CLI flag outputting structured JSON."""
    create_searchable_pdf(tmp_path / "books" / "book-a.pdf")
    extractor_py = SCRIPTS_DIR / "extractor.py"

    cmd = [
        sys.executable,
        str(extractor_py),
        "auto-ingest",
        "--workspace",
        str(tmp_path),
        "--json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["total_extracted"] == 1


def test_tc_extract_cli_dispatch(tmp_path: Path):
    """Verify tc.py extract dispatches cleanly to auto-ingest."""
    create_searchable_pdf(tmp_path / "books" / "book-b.pdf")
    tc_py = SCRIPTS_DIR / "tc.py"

    cmd = [
        sys.executable,
        str(tc_py),
        "extract",
        "--workspace",
        str(tmp_path),
        "--json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["total_extracted"] == 1
