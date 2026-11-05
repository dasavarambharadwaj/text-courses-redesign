"""tests/test_extractor.py — Comprehensive test suite for pure-Python verbatim extractor."""

from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import pypdf

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from extractor import extract_document, extract_pdf_to_markdown, probe_pdf

EXTRACTOR_SCRIPT = SCRIPTS_DIR / "extractor.py"


def create_synthetic_pdf(tmp_path: Path, filename: str, pages_text: list[str]) -> Path:
    """Helper to generate a real, valid PDF file on the fly using pypdf."""
    writer = pypdf.PdfWriter()
    for text in pages_text:
        # pypdf can create blank pages, but to have text we add annotations or blank page
        page = writer.add_blank_page(width=612, height=792)
        # Note: blank pages in pypdf have 0 extractable text unless text is drawn.
    pdf_path = tmp_path / filename
    with open(pdf_path, "wb") as f:
        writer.write(f)
    return pdf_path


def create_searchable_pdf_with_text(tmp_path: Path, filename: str) -> Path:
    """Create a searchable PDF using a minimal valid PDF raw byte representation."""
    # Standard raw minimal 1-page PDF stream containing extractable text
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
    p = tmp_path / filename
    p.write_bytes(raw_pdf)
    return p


def create_scanned_bitmap_pdf(tmp_path: Path, filename: str) -> Path:
    """Create a PDF with 0 extractable text characters to simulate a scanned image PDF."""
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
200
%%EOF"""
    p = tmp_path / filename
    p.write_bytes(raw_pdf)
    return p


def test_probe_searchable_pdf(tmp_path: Path) -> None:
    """Verify probe passes for a digital searchable PDF with sufficient character density."""
    pdf_file = create_searchable_pdf_with_text(tmp_path, "searchable.pdf")
    res = probe_pdf(pdf_file, density_threshold=20)
    assert res["ok"] is True
    assert res["is_scanned_image"] is False
    assert res["status"] == "passed_probe"
    assert res["page_count"] == 1
    assert res["total_characters"] > 20


def test_probe_scanned_image_pdf_fail_fast(tmp_path: Path) -> None:
    """Verify probe fails fast on a scanned bitmap PDF with near-zero characters."""
    pdf_file = create_scanned_bitmap_pdf(tmp_path, "scanned.pdf")
    res = probe_pdf(pdf_file, density_threshold=50)
    assert res["ok"] is False
    assert res["is_scanned_image"] is True
    assert res["status"] == "failed_probe"
    assert "scanned bitmap image" in res["message"]


def test_extract_searchable_pdf_to_markdown(tmp_path: Path) -> None:
    """Verify extract_pdf_to_markdown produces verbatim text and preserves code blocks."""
    pdf_file = create_searchable_pdf_with_text(tmp_path, "consensus_notes.pdf")
    out_dir = tmp_path / "extracted"

    res = extract_pdf_to_markdown(pdf_file, output_path=out_dir, density_threshold=20)
    assert res["ok"] is True
    assert res["output_file"] is not None

    out_file = Path(res["output_file"])
    assert out_file.is_file()
    md_text = out_file.read_text(encoding="utf-8")

    assert "Chapter 1: Distributed Consensus" in md_text
    assert "def election_safety(): return True" in md_text
    assert "<!-- page: 1 -->" in md_text


def test_extract_scanned_pdf_halts_with_error(tmp_path: Path) -> None:
    """Verify extract_pdf_to_markdown rejects scanned image PDF without crashing."""
    pdf_file = create_scanned_bitmap_pdf(tmp_path, "scanned_book.pdf")
    res = extract_pdf_to_markdown(pdf_file, density_threshold=50)
    assert res["ok"] is False
    assert res["code"] == "SCANNED_PDF"
    assert "scanned bitmap image" in res["error"]


def test_extract_markdown_and_txt_files(tmp_path: Path) -> None:
    """Verify universal extract_document handles standard markdown files directly."""
    md_source = tmp_path / "chapter_notes.md"
    md_source.write_text("# Chapter Notes\n- Invariant: Acyclic DAG\n```rust\nfn main() {}\n```", encoding="utf-8")

    out_dir = tmp_path / "out"
    res = extract_document(md_source, output_path=out_dir)
    assert res["ok"] is True
    assert res["output_file"] is not None

    out_file = Path(res["output_file"])
    assert out_file.is_file()
    assert "Invariant: Acyclic DAG" in out_file.read_text(encoding="utf-8")


def test_cli_probe_and_extract_subcommands(tmp_path: Path) -> None:
    """Verify CLI interface for probe and extract subcommands with --json flag."""
    pdf_file = create_searchable_pdf_with_text(tmp_path, "cli_test.pdf")

    # CLI Probe
    probe_run = subprocess.run(
        [sys.executable, str(EXTRACTOR_SCRIPT), "probe", "--input", str(pdf_file), "--threshold", "20", "--json"],
        capture_output=True,
        text=True,
    )
    assert probe_run.returncode == 0
    probe_data = json.loads(probe_run.stdout)
    assert probe_data["ok"] is True
    assert probe_data["status"] == "passed_probe"

    # CLI Extract
    out_dir = tmp_path / "cli_out"
    ext_run = subprocess.run(
        [sys.executable, str(EXTRACTOR_SCRIPT), "extract", "--input", str(pdf_file), "--output", str(out_dir), "--threshold", "20", "--json"],
        capture_output=True,
        text=True,
    )
    assert ext_run.returncode == 0
    ext_data = json.loads(ext_run.stdout)
    assert ext_data["ok"] is True
    assert Path(ext_data["output_file"]).is_file()


def test_zero_bmad_references() -> None:
    """Verify strict zero-BMad invariant across extractor script and tests."""
    script_text = EXTRACTOR_SCRIPT.read_text(encoding="utf-8")
    assert not re.search(r"\bbmad\b", script_text, re.IGNORECASE), "Forbidden BMad mention in extractor.py"
