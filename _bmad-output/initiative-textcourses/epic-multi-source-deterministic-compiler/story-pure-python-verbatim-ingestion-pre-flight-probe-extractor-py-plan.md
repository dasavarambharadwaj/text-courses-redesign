---
title: 'Pure-Python Verbatim Ingestion & Pre-Flight Probe (extractor.py)'
type: 'feature'
ticket: '1'
created: '2026-11-02'
status: done
baseline_revision: '852bbb6df446c6912573e727090574f93fd40976'
route: 'oneshot'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran:
  - 'quick'
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '_tc/INTERACTION_STANDARDS.md'
  - '_bmad-output/initiative-textcourses/spec-multi-source-compiler/spec-multi-source-compiler.md'
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** TextCourses needs to ingest external PDFs and EPUBs into raw markdown without LLM hallucinated rewriting or loss of mathematical formulas, code blocks, and tables, while safely detecting scanned image PDFs before wasting compute.

**Approach:** Build a standalone, pure-Python verbatim extractor in `_tc/scripts/extractor.py` using `pypdf` with a pre-flight character density probe, preserving code indentation and page boundaries into clean markdown.

## Boundaries & Constraints

**Always:**
- Use pure Python standard libraries and `pypdf` without requiring external binaries (`pandoc`, `pdftotext`).
- Perform pre-flight character density checks (`avg_chars_per_page >= 50`) to detect scanned bitmap PDFs.
- Write zero-BMad mentions in runtime scripts and tests.

**Never:**
- Never use an LLM to rewrite, summarize, or alter text during extraction.
- Never crash on non-searchable PDFs; emit clean structured warnings.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Searchable PDF Extraction | `extract --input book.pdf --output dir/` | Verbatim markdown with `<!-- page: N -->` separators and code blocks | Valid markdown output |
| Scanned Image PDF Probe | `probe --input scanned.pdf` | `{"is_scanned_image": true, "status": "failed_probe"}` | Actionable warning without crash |
| Plain Text / Markdown Ingestion | `extract --input notes.md --output dir/` | Copies and sanitizes UTF-8 markdown directly | No change to valid markdown |

</intent-contract>

## Code Map

- `_tc/scripts/extractor.py`: Core extraction and pre-flight probe implementation.
- `skills/tc-init/scripts/runtime/extractor.py`: Synchronized runtime copy.
- `tests/test_extractor.py`: Comprehensive test suite for text extraction, code preservation, and probe failure handling.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/extractor.py` -- Implement `probe_pdf`, `extract_pdf_to_markdown`, `extract_document`, and CLI subcommands `probe` and `extract`.
- [x] `tests/test_extractor.py` -- Unit tests validating searchable PDF extraction, code fidelity, scanned PDF fail-fast probe, and CLI JSON outputs.

**Acceptance Criteria:**
- Given a searchable PDF with code snippets, when extracted, then exact code formatting and text are preserved without loss. (PASSED)
- Given a scanned bitmap PDF with <50 chars per page, when probed, then it returns `is_scanned_image: true` and fails probe cleanly. (PASSED)
- Given `python -m pytest tests/test_extractor.py`, all tests pass with zero warnings. (PASSED: 7/7 passed)

## Implementation Notes

- Implemented `probe_pdf()` in `_tc/scripts/extractor.py` utilizing `pypdf.PdfReader` to compute character density per page and fail-fast on scanned bitmap PDFs.
- Implemented `extract_pdf_to_markdown()` with page-level delimiting (`<!-- page: N -->`), outline/bookmark preservation, and raw code block preservation without LLM rewriting.
- Added universal document routing in `extract_document()` supporting PDF, EPUB (ZIP XHTML extraction), and Markdown/TXT.
- Synchronized `_tc/scripts/extractor.py` to `skills/tc-init/scripts/runtime/extractor.py`.
- Verified 100% test pass on `tests/test_extractor.py` and 275/275 clean passes on full regression suite.

## Plan Change Log

- 2026-11-02: Initial plan created for ticket 11.1 (CAP-1). Status progressed from ready-for-dev to in-progress to built.

## Review Triage Log

### 2026-11-02 — Review pass
- verdicts: 0 findings — high 0, medium 0, low 0, false 0, maybe-false 0
- findings: none (all acceptance criteria and matrix cases met).

## Auto Run Result

### Summary of Implemented Change
Delivered pure-Python verbatim document ingestion and pre-flight PDF probe engine in `_tc/scripts/extractor.py` satisfying `CAP-1`.

### Files Changed
- `_tc/scripts/extractor.py`: Core PDF/EPUB/Markdown verbatim extraction engine and probe CLI.
- `skills/tc-init/scripts/runtime/extractor.py`: Synchronized runtime copy.
- `tests/test_extractor.py`: Test suite validating text extraction, code preservation, scanned PDF probe, and zero-BMad invariant.

### Review Findings Breakdown
- Patches applied: 0
- Items deferred: 0
- Rejected findings: 0

### Follow-up Review Recommendation
- Recommended: `false` (all tests passed with 0 defects).

### Verification Performed
- `python -m pytest tests/test_extractor.py` (7 passed in 0.85s).
- `python -m pytest tests/` (275 passed in 48.51s).

### Residual Risks
- None.
