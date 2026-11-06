---
title: "Zero-Loss Markdown Conversion & Conversion Coverage Ledger Engine"
ticket: 11
status: done
epic: epic-consumer-ux-and-unified-tc
covers: [CAP-3, FR-48]
completed_at: "2026-11-06T20:50:00+05:30"
---

# Story 12.11: Zero-Loss Markdown Conversion & Conversion Coverage Ledger Engine (CAP-3, FR-48)

## Summary
Implemented the pure-Python zero-loss multi-format converter and conversion coverage ledger engine under `_tc/scripts/extractor.py`. Converts multi-format research sources (PDF, EPUB, DOCX, HTML, Jupyter Notebooks, speech transcripts, source code, schemas, and Markdown) into clean verbatim Markdown under `_tc/research/<slug>/sources/markdown/` with 100% text coverage and emits `conversion-ledger.json` and `conversion-ledger.md` mathematically proving character-level ingestion.

## Architectural Changes & Implementation Details
1. **Multi-Format Verbatim Extractors (`_tc/scripts/extractor.py`)**:
   - Implemented `extract_docx_to_markdown` using pure-Python `zipfile` + `xml.etree.ElementTree` without external dependencies.
   - Implemented `extract_html_to_markdown` converting HTML/XHTML to Markdown with image tag omission tracking.
   - Implemented `extract_notebook_to_markdown` converting `.ipynb` markdown and code cells.
   - Implemented `extract_transcript_to_markdown` converting `.vtt` and `.srt` subtitle files into clean speech text.
   - Implemented `extract_code_to_markdown` wrapping languages (`.py`, `.rs`, `.ts`, `.go`, `.c`, etc.) in fenced Markdown blocks.
   - Expanded `extract_document` to route all supported formats with SHA-256 and character count tracking.
2. **Batch Source Conversion & Ledger Engine (`_tc/scripts/extractor.py`)**:
   - Implemented `convert_sources_to_markdown(slug, workspace, density_threshold)`.
   - Populates `_tc/research/<slug>/sources/markdown/` (with legacy mirror).
   - Generates `_tc/research/<slug>/conversion-ledger.json` and `_tc/research/<slug>/conversion-ledger.md`.
   - Records: source path, SHA-256 hash, format, input chars, output chars, omissions (e.g. non-text image media), text coverage percentage, and status.
   - Enforces fail-fast behavior on scanned bitmap PDFs or missing digital text layers.
3. **Dispatcher Integration (`_tc/scripts/tc.py`)**:
   - In interactive mode on source approval (`proceed_open`), automatically triggers `convert_sources_to_markdown`.
   - In auto mode, automatically runs conversion right after scout discovery.

## Verification
- Created `tests/test_conversion_coverage.py` (4 tests, 100% passed):
  - `test_multi_format_extractors_pure_python`
  - `test_convert_sources_to_markdown_and_ledger`
  - `test_scanned_pdf_fails_fast_in_conversion_ledger`
  - `test_tc_dispatch_generates_conversion_ledger`
- Verified regression suite (`tests/test_source_approval_loop.py`): 5 passed.
