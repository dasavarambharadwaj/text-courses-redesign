---
type: epic
title: "Multi-Source Deterministic Compiler and Grounded Sensei Engine"
parent: initiative-textcourses
covers: [CAP-1, CAP-2, CAP-3, CAP-4, CAP-5, CAP-6]
after: [epic-sovereign-knowledge-harvest-and-rag-engine]
assignee: ""
status: done
risk: high
---

# Epic 11: Multi-Source Deterministic Compiler & Grounded Sensei Engine

**Initiative**: `initiative-textcourses`  
**Slug**: `epic-multi-source-deterministic-compiler`  
**Status**: done  
**Covers**: CAP-1, CAP-2, CAP-3, CAP-4, CAP-5, CAP-6  
**References**:
- Spec: `_bmad-output/initiative-textcourses/spec-multi-source-compiler/spec-multi-source-compiler.md`
- Diagrams: `_bmad-output/initiative-textcourses/spec-multi-source-compiler/architecture-diagrams.md`
- Schemas: `_bmad-output/initiative-textcourses/spec-multi-source-compiler/source-map-schema.md`
- Policy: `_bmad-output/initiative-textcourses/spec-multi-source-compiler/vocabulary-contract.md`

## Executive Summary
This epic discards runtime probabilistic RAG for structured course delivery and implements the **Multi-Source Deterministic Compiler**:

1. **Pure-Python Verbatim Ingestion (`CAP-1`)**:
   - `_tc/scripts/extractor.py`: Extracts raw prose, code blocks, tables, and headers from PDFs/EPUBs directly into markdown using `pypdf` / `pdfplumber` with strictly zero LLM rewriting.
   - Pre-flight character density probe to detect non-searchable scanned image PDFs and fail-fast with actionable guidance.

2. **Macro Semantic TOC Alignment & Multi-Source Deduplication (`CAP-2`)**:
   - Extracts Table of Contents ASTs (`toc.json`) across heterogeneous peer sources without LLM token bloat.
   - Clusters overlapping domain primitives (e.g. LSM-Trees, Quorums) so common concepts are taught exactly once in the master DAG, while preserving source-unique niche topics.

3. **Conveyor-Belt Chapter Pipeline & Symbol Table (`CAP-3`, `CAP-4`)**:
   - Ingests multi-hundred-page textbooks sequentially chapter-by-chapter with running vocabulary accumulation, bounding peak prompt tokens below 25,000 to eliminate context window rot.
   - Compiles `courses/<slug>/source-map.toml` mapping every concept to exact source files, heading breadcrumbs, and line spans for $O(1)$ deterministic pointer retrieval during teaching.

4. **Complete Coverage Verification Ledger (`CAP-5`)**:
   - Mathematical audit matrix in `courses/<slug>/coverage-ledger.md` matching every chapter and section of source books to course sections, failing course validation if any section was dropped.

5. **Grounded Sensei Runtime Grounding & Vocabulary Contract (`CAP-6`)**:
   - Updates `teach_engine.py` to load pre-mapped excerpts in under 5ms without runtime search miss rates.
   - Enforces the Vocabulary Contract (two-token rule, intuition-before-label) and synthesizes multi-source differences as dialectic comparisons rather than competing jargon.

## Done When
1. `extractor.py` extracts raw text and code from multi-page PDFs with 100% symbol fidelity and fails fast on scanned bitmaps.
2. Ingesting multiple overlapping books produces a unified, deduplicated DAG where common concepts appear once and unique topics are preserved.
3. Multi-chapter books are ingested through the conveyor belt with peak prompt tokens strictly under 25,000 per step.
4. `source-map.toml` links 100% of concepts in `lesson-plan.md` to valid line ranges, and `teach_engine.py session` loads them via $O(1)$ direct lookup.
5. `coverage-ledger.md` verifies 100% source section coverage and halts compilation on omissions.
6. `teach_engine.py` validates that no unintroduced technical jargon appears in instructional turns.
7. Full unit and integration test suite passes with zero regressions.

## Stories Breakdown
1. `story-pure-python-verbatim-ingestion-and-preflight-probe` (CAP-1)
2. `story-macro-semantic-toc-alignment-and-deduplication-engine` (CAP-2)
3. `story-conveyor-belt-chapter-pipeline-and-symbol-table` (CAP-3, CAP-4)
4. `story-complete-coverage-verification-ledger` (CAP-5)
5. `story-grounded-sensei-runtime-grounding-and-vocabulary-contract` (CAP-6)
6. `story-refactor-sweep-cli-integration-and-e2e-test-suite` (CAP-1, CAP-2, CAP-3, CAP-4, CAP-5, CAP-6)
