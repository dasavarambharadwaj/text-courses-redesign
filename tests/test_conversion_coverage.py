#!/usr/bin/env python3
"""tests/test_conversion_coverage.py — Zero-loss conversion & conversion coverage ledger engine tests (FR-48, CAP-3)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
import pytest

from _tc.scripts import extractor, bootstrapper, tc


def create_mock_docx(path: Path, title: str, paragraphs: list[str]) -> Path:
    """Create a minimal valid DOCX file without third-party dependencies."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body_xml_parts = [
        f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>{title}</w:t></w:r></w:p>'
    ]
    for p in paragraphs:
        body_xml_parts.append(f'<w:p><w:r><w:t>{p}</w:t></w:r></w:p>')

    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
        '<w:body>\n'
        + "".join(body_xml_parts)
        + "\n</w:body></w:document>"
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", doc_xml.encode("utf-8"))
        z.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')

    return path


def test_multi_format_extractors_pure_python(tmp_path: Path) -> None:
    """Verify type-specific extractors produce zero-loss Markdown for DOCX, HTML, Notebooks, and Code."""
    # 1. DOCX
    docx_path = tmp_path / "architecture.docx"
    create_mock_docx(docx_path, "System Architecture", ["Invariants are absolute.", "Transactions require WAL."])
    docx_res = extractor.extract_document(docx_path)
    assert docx_res["ok"] is True
    assert docx_res["format"] == "docx"
    assert docx_res["text_coverage_pct"] == 100.0
    assert "System Architecture" in docx_res["markdown"]
    assert "Invariants are absolute." in docx_res["markdown"]

    # 2. HTML
    html_path = tmp_path / "guide.html"
    html_path.write_text(
        "<html><body><h1>Protocol Spec</h1><p>The state machine must be deterministic.</p><img src='chart.png'/></body></html>",
        encoding="utf-8",
    )
    html_res = extractor.extract_document(html_path)
    assert html_res["ok"] is True
    assert html_res["format"] == "html"
    assert html_res["text_coverage_pct"] == 100.0
    assert html_res["omitted_images_count"] == 1
    assert "Protocol Spec" in html_res["markdown"]
    assert "The state machine must be deterministic." in html_res["markdown"]

    # 3. Jupyter Notebook (.ipynb)
    nb_path = tmp_path / "simulation.ipynb"
    nb_data = {
        "cells": [
            {"cell_type": "markdown", "source": ["# Simulation\n", "Run paxos consensus algorithm."]},
            {"cell_type": "code", "source": ["def run_consensus():\n", "    return True\n"]},
        ]
    }
    nb_path.write_text(json.dumps(nb_data), encoding="utf-8")
    nb_res = extractor.extract_document(nb_path)
    assert nb_res["ok"] is True
    assert nb_res["format"] == "ipynb"
    assert nb_res["text_coverage_pct"] == 100.0
    assert "def run_consensus():" in nb_res["markdown"]

    # 4. Source Code (.rs)
    rs_path = tmp_path / "engine.rs"
    rs_path.write_text("pub struct RaftNode {\n    term: u64,\n}\n", encoding="utf-8")
    rs_res = extractor.extract_document(rs_path)
    assert rs_res["ok"] is True
    assert rs_res["format"] == "rs"
    assert "```rust" in rs_res["markdown"]
    assert "pub struct RaftNode" in rs_res["markdown"]

    # 5. Transcript (.vtt)
    vtt_path = tmp_path / "lecture.vtt"
    vtt_path.write_text("WEBVTT\n\n1\n00:00:01.000 --> 00:00:04.000\nToday we study distributed consensus.\n", encoding="utf-8")
    vtt_res = extractor.extract_document(vtt_path)
    assert vtt_res["ok"] is True
    assert "Today we study distributed consensus." in vtt_res["markdown"]


def test_convert_sources_to_markdown_and_ledger(tmp_path: Path) -> None:
    """Verify batch source conversion under _tc/research/<slug>/sources/markdown/ and emission of conversion ledger."""
    slug = "raft-consensus"
    sources_dir = tmp_path / "_tc" / "research" / slug / "sources"
    (sources_dir / "rfcs").mkdir(parents=True, exist_ok=True)
    (sources_dir / "docs").mkdir(parents=True, exist_ok=True)
    (sources_dir / "repos").mkdir(parents=True, exist_ok=True)

    # Populate sources
    (sources_dir / "rfcs" / "paxos_spec.txt").write_text("Paxos achieves consensus in asynchronous networks.", encoding="utf-8")
    (sources_dir / "docs" / "raft_overview.md").write_text("# Raft Consensus\nLeader election and log replication.", encoding="utf-8")
    create_mock_docx(sources_dir / "docs" / "distributed_notes.docx", "Consensus Rules", ["Quorum must intersect."])
    (sources_dir / "repos" / "raft_impl.py").write_text("class RaftState:\n    LEADER = 1\n", encoding="utf-8")

    res = extractor.convert_sources_to_markdown(slug, workspace=tmp_path)
    assert res["ok"] is True
    assert res["total_sources"] == 4
    assert res["global_text_coverage_pct"] == 100.0

    # Verify markdown directory
    md_dir = tmp_path / "_tc" / "research" / slug / "sources" / "markdown"
    assert md_dir.is_dir()
    assert (md_dir / "paxos_spec.md").is_file()
    assert (md_dir / "raft_overview.md").is_file()
    assert (md_dir / "distributed_notes.md").is_file()
    assert (md_dir / "raft_impl.md").is_file()

    # Verify ledger json & md
    ledger_json = tmp_path / "_tc" / "research" / slug / "conversion-ledger.json"
    ledger_md = tmp_path / "_tc" / "research" / slug / "conversion-ledger.md"
    assert ledger_json.is_file()
    assert ledger_md.is_file()

    data = json.loads(ledger_json.read_text(encoding="utf-8"))
    assert data["status"] == "verified_zero_loss"
    assert data["global_text_coverage_pct"] == 100.0
    assert len(data["sources"]) == 4

    md_text = ledger_md.read_text(encoding="utf-8")
    assert "Zero-Loss Conversion Coverage Ledger" in md_text
    assert "VERIFIED ZERO-LOSS" in md_text
    assert "| `_tc/research/raft-consensus/sources/rfcs/paxos_spec.txt`" in md_text or "paxos_spec" in md_text


def test_scanned_pdf_fails_fast_in_conversion_ledger(tmp_path: Path) -> None:
    """Verify scanned bitmap PDFs trigger fail-fast probe warnings in the conversion ledger."""
    slug = "scanned-course"
    sources_dir = tmp_path / "_tc" / "research" / slug / "sources" / "docs"
    sources_dir.mkdir(parents=True, exist_ok=True)

    # Empty mock PDF fails probe
    bad_pdf = sources_dir / "scanned_doc.pdf"
    bad_pdf.write_bytes(b"%PDF-1.4\n%EOF\n")

    res = extractor.convert_sources_to_markdown(slug, workspace=tmp_path)
    # Fails fast on unparseable/scanned PDF without digital text
    assert res["ok"] is False or len(res.get("failed_probes", [])) > 0
    ledger_md = tmp_path / "_tc" / "research" / slug / "conversion-ledger.md"
    assert ledger_md.is_file()


def test_tc_dispatch_generates_conversion_ledger(tmp_path: Path) -> None:
    """Verify /tc dispatch generates zero-loss conversion ledger upon source approval."""
    bootstrapper.bootstrap_workspace(path=tmp_path, mode="interactive")

    # Turn 1: Enter topic
    turn_1 = tc.dispatch_conversational_turn("Distributed Systems", workspace=tmp_path)
    assert turn_1["state"] == "acquisition_gate"

    # Turn 2: Approve sources
    turn_2 = tc.dispatch_conversational_turn("1", workspace=tmp_path)
    assert turn_2["state"] == "blueprint"

    # Verify conversion ledger generated automatically
    ledger_md = tmp_path / "_tc" / "research" / "distributed-systems" / "conversion-ledger.md"
    assert ledger_md.is_file(), "Conversion ledger was not generated upon source approval"
    content = ledger_md.read_text(encoding="utf-8")
    assert "Zero-Loss Conversion Coverage Ledger" in content
    assert "VERIFIED ZERO-LOSS" in content
